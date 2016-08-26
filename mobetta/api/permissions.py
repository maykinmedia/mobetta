from rest_framework import permissions

from mobetta.access import can_translate


class CanTranslatePermission(permissions.BasePermission):
    """
    Applies translation permissions to API.
    """

    def has_permission(self, request, view):
        return can_translate(request.user)
