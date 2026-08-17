from rest_framework import permissions


class IsWarehouseStaff(permissions.BasePermission):

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return bool(
            request.user.is_superuser
            or request.user.is_staff
            or getattr(request.user, "role", None)
            in ["ADMIN", "WAREHOUSE_MANAGER", "MANAGER"]
        )


class IsWarehouseStaffOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(
            request.user.is_superuser
            or request.user.is_staff
            or getattr(request.user, "role", None)
            in ["ADMIN", "WAREHOUSE_MANAGER", "MANAGER"]
        )
