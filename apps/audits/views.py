from django.db import transaction
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from apps.projects.models import Project
from apps.audits.models import Audit, AuditStatus
from apps.audits.serializers import AuditSerializer, URLSubmitSerializer
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
                filter=Q(status=AuditStatus.COMPLETED, seo_score__isnull=False)
            ),
            missing_titles=Count(
                "id",
                filter=Q(title__isnull=True) | Q(title="")
            ),
            missing_meta_descriptions=Count(
                "id",
                filter=Q(meta_description__isnull=True) | Q(meta_description="")
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