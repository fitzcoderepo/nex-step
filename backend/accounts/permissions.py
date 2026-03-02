from rest_framework.permissions import BasePermission
from accounts.models import User


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Roles.OWNER
    

class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.Roles.OWNER, User.Roles.ADMIN]
    
class IsAuthorOrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.Roles.OWNER, User.Roles.ADMIN, User.Roles.AUTHOR]