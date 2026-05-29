from django.db import models
from apps.projects.models import Project


class AuditStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Audit(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="audits"
    )

    url = models.URLField(max_length=1000)
    status = models.CharField(
        max_length=20,
        choices=AuditStatus.choices,
        default=AuditStatus.PENDING
    )

    title = models.CharField(max_length=500, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    h1_count = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0)
    seo_score = models.PositiveIntegerField(blank=True, null=True)

    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "url"],
                name="unique_audit_url_per_project"
            )
        ]

    def __str__(self):
        return f"{self.url} - {self.status}"