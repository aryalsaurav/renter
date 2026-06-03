from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Read access to anyone; write access only to the listing's owner."""

    message = "You can only modify your own listings."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "owner", None) or getattr(
            getattr(obj, "listing", None), "owner", None
        )
        return owner == request.user
