from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.audits.views import AuditViewSet

router = DefaultRouter()
router.register(r"", AuditViewSet, basename="audits")

urlpatterns = [
    path("", include(router.urls)),
]