from django.contrib import admin
from apps.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "domain", "owner", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "domain", "owner__username", "owner__email"]
    readonly_fields = ["created_at", "updated_at"]