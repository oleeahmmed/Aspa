# আপনার cardealing/api/urls.py file টি এভাবে replace করুন:

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

# Create router and register viewsets
router = DefaultRouter()

# Authentication
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'groups', views.GroupViewSet, basename='group')

# User Profiles
router.register(r'customer-profiles', views.CustomerProfileViewSet, basename='customerprofile')
router.register(r'subscription-plans', views.SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'dealer-profiles', views.DealerProfileViewSet, basename='dealerprofile')
router.register(r'commission-history', views.CommissionHistoryViewSet, basename='commissionhistory')

# Vehicle Management
router.register(r'vehicle-makes', views.VehicleMakeViewSet, basename='vehiclemake')
router.register(r'vehicle-models', views.VehicleModelViewSet, basename='vehiclemodel')
router.register(r'vehicles', views.VehicleViewSet, basename='vehicle')

# Service Management
router.register(r'service-categories', views.ServiceCategoryViewSet, basename='servicecategory')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'service-addons', views.ServiceAddonViewSet, basename='serviceaddon')
router.register(r'technicians', views.TechnicianViewSet, basename='technician')
router.register(r'service-slots', views.ServiceSlotViewSet, basename='serviceslot')

# Booking System
router.register(r'cancellation-policies', views.CancellationPolicyViewSet, basename='cancellationpolicy')
router.register(r'promotions', views.PromotionViewSet, basename='promotion')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'booking-status-history', views.BookingStatusHistoryViewSet, basename='bookingstatushistory')

# Payment System
router.register(r'virtual-cards', views.VirtualCardViewSet, basename='virtualcard')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'dealer-payouts', views.DealerPayoutViewSet, basename='dealerpayout')

# Communication
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'reviews', views.ReviewViewSet, basename='review')

# Support System
router.register(r'support-tickets', views.SupportTicketViewSet, basename='supportticket')
router.register(r'support-messages', views.SupportMessageViewSet, basename='supportmessage')

# Analytics
router.register(r'booking-analytics', views.BookingAnalyticsViewSet, basename='bookinganalytics')
router.register(r'dealer-analytics', views.DealerAnalyticsViewSet, basename='dealeranalytics')

# System
router.register(r'system-configuration', views.SystemConfigurationViewSet, basename='systemconfiguration')
router.register(r'admin-actions', views.AdminActionViewSet, basename='adminaction')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # ✅ dj-rest-auth endpoints (JWT enabled)
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # ✅ JWT token refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ✅ Mobile-optimized social auth
    path('auth/google/', views.CustomGoogleLoginView.as_view(), name='google_login'),
    path('auth/facebook/', views.CustomFacebookLoginView.as_view(), name='facebook_login'),
    path('auth/apple/', views.CustomAppleLoginView.as_view(), name='apple_login'),
    
    # ✅ Profile management
    path('auth/create-dealer-profile/', views.create_dealer_profile, name='create_dealer_profile'),
    
    # Legacy token auth (keep for backward compatibility)
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='api_register'),
]