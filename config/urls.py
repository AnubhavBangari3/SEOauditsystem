from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/audits/", include("apps.audits.urls")),
]