from django.conf import settings
from django.db import models


class Project(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects"
    )
    name = models.CharField(max_length=255)
    domain = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "domain"],
                name="unique_project_domain_per_user"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.domain}"