from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from apps.projects.models import Project
from apps.audits.models import Audit
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
