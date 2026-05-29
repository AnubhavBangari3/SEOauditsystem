from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects.models import Project
from apps.audits.models import Audit
from apps.audits.serializers import AuditSerializer, URLSubmitSerializer
from apps.audits.permissions import IsAuditOwner


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditSerializer
    permission_classes = [IsAuthenticated, IsAuditOwner]

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

        audits = [
            Audit(project=project, url=url)
            for url in serializer.validated_data["urls"]
        ]

        created_audits = Audit.objects.bulk_create(audits)

        response_serializer = AuditSerializer(
            created_audits,
            many=True
        )

        return Response(
            {
                "message": "URLs submitted successfully.",
                "count": len(created_audits),
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )