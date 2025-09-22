from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermissionMetaclass):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True 
        return obj.user == request.user or request.user.is_staff or request.user.is_superuser
    
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)