from rest_framework.permissions import BasePermission


class IsAuditOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.project.owner == request.user