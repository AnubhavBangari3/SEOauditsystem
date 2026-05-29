from rest_framework import serializers
from apps.projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "domain", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_domain(self, value):
        value = value.strip().lower()

        request = self.context.get("request")
        user = request.user if request else None

        existing_project = Project.objects.filter(
            owner=user,
            domain=value
        )

        if self.instance:
            existing_project = existing_project.exclude(id=self.instance.id)

        if existing_project.exists():
            raise serializers.ValidationError(
                "You already have a project with this domain."
            )

        return value