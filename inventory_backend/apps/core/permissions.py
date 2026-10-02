from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_in_groups(user, *groups) -> bool:
    return user.is_superuser or user.groups.filter(name__in=groups).exists()


class ReadOnlyOrRole(BasePermission):
    """Lectura: cualquier autenticado. Escritura: solo los roles indicados en la vista (write_roles)."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user_in_groups(request.user, *getattr(view, "write_roles", ()))


class DeleteRole(BasePermission):
    """Borrado: solo los roles de la vista (delete_roles)."""
    def has_permission(self, request, view):
        if request.method != "DELETE":
            return True
        return user_in_groups(request.user, *getattr(view, "delete_roles", ()))