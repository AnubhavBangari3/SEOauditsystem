from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer
from apps.projects.permissions import IsProjectOwner


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        """
        User isolation:
        Logged-in users can only see their own projects.
        """
        return Project.objects.filter(
            owner=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        """
        Automatically attach logged-in user as project owner.
        User cannot create project for another user.
        """
        serializer.save(owner=self.request.user)