from rest_framework import permissions
from django.contrib.auth.models import User


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsDealerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow dealers or admin users.
    """
    
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        
        return hasattr(request.user, 'dealer_profile')


class IsCustomer(permissions.BasePermission):
    """
    Custom permission to only allow customers.
    """
    
    def has_permission(self, request, view):
        return hasattr(request.user, 'customer_profile')


class IsApprovedDealer(permissions.BasePermission):
    """
    Custom permission to only allow approved dealers.
    """
    
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        
        if hasattr(request.user, 'dealer_profile'):
            return request.user.dealer_profile.is_approved and request.user.dealer_profile.is_active
        
        return False


class IsBookingParticipant(permissions.BasePermission):
    """
    Custom permission to only allow booking participants (customer or dealer).
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Check if user is the customer
        if obj.customer == request.user:
            return True
        
        # Check if user is the dealer
        if hasattr(request.user, 'dealer_profile') and obj.service_slot.service.dealer == request.user:
            return True
        
        return False


class CanManageService(permissions.BasePermission):
    """
    Custom permission to only allow service owners or admin to manage services.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        return obj.dealer == request.user


class CanViewFinancialData(permissions.BasePermission):
    """
    Custom permission for viewing financial data.
    """
    
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        
        # Dealers can view their own financial data
        return hasattr(request.user, 'dealer_profile')
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Check if the financial data belongs to the dealer
        if hasattr(obj, 'dealer') and obj.dealer == request.user:
            return True
        
        return False
