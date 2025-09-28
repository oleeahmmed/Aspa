# cardealing/permissions.py
from rest_framework import permissions

class CardealingHasDynamicModelPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with the appropriate permissions based on the model.
    """
    def has_permission(self, request, view):
        # Determine the model name dynamically from the viewset.
        model_name = view.queryset.model._meta.model_name
        # Map HTTP methods to permission types.
        if request.method in permissions.SAFE_METHODS:
            perm_action = 'view'
        elif request.method == 'POST':
            perm_action = 'add'
        elif request.method in ['PUT', 'PATCH']:
            perm_action = 'change'
        elif request.method == 'DELETE':
            perm_action = 'delete'
        else:
            return False
        # Check if the user has the required permission.
        required_permission = f'cardealing.{perm_action}_{model_name}'
        return request.user.has_perm(required_permission)
    
    def has_object_permission(self, request, view, obj):
        # Similar to has_permission, but checks permissions on an object level.
        model_name = obj._meta.model_name
        if request.method in permissions.SAFE_METHODS:
            perm_action = 'view'
        elif request.method in ['PUT', 'PATCH']:
            perm_action = 'change'
        elif request.method == 'DELETE':
            perm_action = 'delete'
        else:
            return False
        required_permission = f'cardealing.{perm_action}_{model_name}'
        return request.user.has_perm(required_permission, obj)