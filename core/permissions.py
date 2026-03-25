from rest_framework.permissions import BasePermission

from apps.access.models import AccessRule

_METHOD_TO_FIELD = {
    'GET': 'read',
    'POST': 'create',
    'PATCH': 'update',
    'PUT': 'update',
    'DELETE': 'delete',
}


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.role and request.user.role.name == 'admin')


class RBACPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        element_name = getattr(view, 'rbac_element', None)
        if not element_name or not request.user.role:
            return False

        try:
            rule = AccessRule.objects.get(role=request.user.role, element__name=element_name)
        except AccessRule.DoesNotExist:
            return False

        field = _METHOD_TO_FIELD.get(request.method)
        return bool(field and getattr(rule, field, False))
