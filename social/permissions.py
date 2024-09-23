from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 'admin':
                return True  # Admins can access all
            if request.user.role == 'write':
                # Allow read and write actions
                return request.method in ['GET', 'POST']
            if request.user.role == 'read':
                # Allow only read actions
                return request.method == 'GET'
        return False
