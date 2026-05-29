from rest_framework.permissions import BasePermission


class IsProjectOwner(BasePermission):
    """
    Object-level permission.
    Only project owner can access/update/delete project.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user