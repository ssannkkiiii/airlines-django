from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    
    def has_permission(self, request, view):
        
        return (
            request.user and request.user.is_authenticated 
            and request.user.role == 'admin'
        )
        
class IsAdminOrReadOnly(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and request.user.is_authenticated and 
            request.user.role == 'admin'
        )
        
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user 
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False