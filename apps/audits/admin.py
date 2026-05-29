from django.contrib import admin
from apps.audits.models import Audit


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "url",
        "status",
        "seo_score",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("url", "project__name", "project__owner__username")
    readonly_fields = ("created_at", "updated_at")