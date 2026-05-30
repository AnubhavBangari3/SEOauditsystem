import csv
import io

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects.models import Project
from apps.audits.models import Audit, AuditStatus
from apps.audits.serializers import (
    AuditSerializer,
    URLSubmitSerializer,
    CSVUploadSerializer,
)
from apps.audits.permissions import IsAuditOwner
from apps.audits.tasks import process_audit_task
from apps.audits.filters import AuditFilter
from common.pagination import StandardResultsSetPagination


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditSerializer
    permission_classes = [IsAuthenticated, IsAuditOwner]
    pagination_class = StandardResultsSetPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = AuditFilter
    search_fields = ["url"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "seo_score",
        "word_count",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Audit.objects.filter(
            project__owner=self.request.user
        ).select_related("project")

    @action(
        detail=False,
        methods=["get"],
        url_path="dashboard"
    )
    def dashboard(self, request):
        queryset = self.get_queryset()

        project_id = request.query_params.get("project")

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        metrics = queryset.aggregate(
            total_audited_urls=Count("id"),
            failed_audits=Count(
                "id",
                filter=Q(status=AuditStatus.FAILED)
            ),
            average_seo_score=Avg(
                "seo_score",
                filter=Q(
                    status=AuditStatus.COMPLETED,
                    seo_score__isnull=False
                )
            ),
            missing_titles=Count(
                "id",
                filter=Q(title__isnull=True) | Q(title="")
            ),
            missing_meta_descriptions=Count(
                "id",
                filter=Q(meta_description__isnull=True)
                | Q(meta_description="")
            ),
        )

        return Response(
            {
                "total_audited_urls": metrics["total_audited_urls"] or 0,
                "failed_audits": metrics["failed_audits"] or 0,
                "average_seo_score": round(metrics["average_seo_score"] or 0, 2),
                "missing_titles": metrics["missing_titles"] or 0,
                "missing_meta_descriptions": metrics["missing_meta_descriptions"] or 0,
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="submit/(?P<project_id>[^/.]+)"
    )
    def submit_urls(self, request, project_id=None):
        project = get_object_or_404(
            Project,
            id=project_id,
            owner=request.user
        )

        serializer = URLSubmitSerializer(
            data=request.data,
            context={"project": project}
        )
        serializer.is_valid(raise_exception=True)

        urls = serializer.validated_data["urls"]

        with transaction.atomic():
            audits = [
                Audit(project=project, url=url)
                for url in urls
            ]

            created_audits = Audit.objects.bulk_create(audits)

            transaction.on_commit(
                lambda: [
                    process_audit_task.delay(audit.id)
                    for audit in created_audits
                ]
            )

        response_serializer = AuditSerializer(
            created_audits,
            many=True
        )

        return Response(
            {
                "message": "URLs submitted successfully and audit jobs queued.",
                "count": len(created_audits),
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="upload-csv/(?P<project_id>[^/.]+)",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_csv(self, request, project_id=None):
        project = get_object_or_404(
            Project,
            id=project_id,
            owner=request.user
        )

        serializer = CSVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data["file"]

        try:
            decoded_file = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {
                    "message": "Invalid CSV encoding. Please upload UTF-8 CSV file."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        csv_reader = csv.reader(io.StringIO(decoded_file))
        validator = URLValidator()

        valid_urls = []
        invalid_rows = []
        duplicate_urls = []
        empty_rows = 0
        total_rows = 0

        existing_urls = set(
            Audit.objects.filter(project=project)
            .values_list("url", flat=True)
        )

        for index, row in enumerate(csv_reader, start=1):
            if not row or not row[0].strip():
                empty_rows += 1
                continue

            raw_url = row[0].strip()

            if index == 1 and raw_url.lower() in ["url", "urls"]:
                continue

            total_rows += 1

            try:
                validator(raw_url)
            except ValidationError:
                invalid_rows.append(
                    {
                        "row": index,
                        "url": raw_url,
                        "reason": "Invalid URL format"
                    }
                )
                continue

            if raw_url in existing_urls:
                duplicate_urls.append(
                    {
                        "row": index,
                        "url": raw_url,
                        "reason": "URL already exists in this project"
                    }
                )
                continue

            if raw_url in valid_urls:
                duplicate_urls.append(
                    {
                        "row": index,
                        "url": raw_url,
                        "reason": "Duplicate URL inside uploaded CSV"
                    }
                )
                continue

            valid_urls.append(raw_url)

        if not valid_urls:
            return Response(
                {
                    "message": "CSV processed, but no valid new URLs found.",
                    "total_rows": total_rows,
                    "created": 0,
                    "queued": 0,
                    "invalid_count": len(invalid_rows),
                    "duplicate_count": len(duplicate_urls),
                    "empty_rows": empty_rows,
                    "invalid_rows": invalid_rows,
                    "duplicate_urls": duplicate_urls,
                },
                status=status.HTTP_200_OK
            )

        with transaction.atomic():
            audits = [
                Audit(project=project, url=url)
                for url in valid_urls
            ]

            created_audits = Audit.objects.bulk_create(audits)

            transaction.on_commit(
                lambda: [
                    process_audit_task.delay(audit.id)
                    for audit in created_audits
                ]
            )

        response_serializer = AuditSerializer(created_audits, many=True)

        return Response(
            {
                "message": "CSV processed successfully. Valid URLs queued for audit.",
                "total_rows": total_rows,
                "created": len(created_audits),
                "queued": len(created_audits),
                "invalid_count": len(invalid_rows),
                "duplicate_count": len(duplicate_urls),
                "empty_rows": empty_rows,
                "invalid_rows": invalid_rows,
                "duplicate_urls": duplicate_urls,
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )