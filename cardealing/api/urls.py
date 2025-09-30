from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

urlpatterns = [
    # =============================================================================
    # AUTHENTICATION
    # =============================================================================
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),

    path('auth/jwt/login/', views.CustomTokenObtainPairView.as_view(), name='jwt_login'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('auth/me/', views.CurrentUserView.as_view(), name='current_user'),
    
    # Users (Admin)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    
    # =============================================================================
    # USER PROFILES
    # =============================================================================
    path('profile/customer/', views.CustomerProfileView.as_view(), name='customer_profile'),
    path('profile/dealer/', views.DealerProfileView.as_view(), name='dealer_profile'),
    path('dealers/', views.DealerProfileListView.as_view(), name='dealer_list'),
    
    path('subscription-plans/', views.SubscriptionPlanListView.as_view(), name='subscription_plans'),
    path('subscription-plans/<int:pk>/', views.SubscriptionPlanDetailView.as_view(), name='subscription_plan_detail'),
    
    path('commission-history/', views.CommissionHistoryListView.as_view(), name='commission_history'),
    
    path('customer-verifications/', views.CustomerVerificationListView.as_view(), name='customer_verifications'),
    
    path('dealer-verification-documents/', views.DealerVerificationDocumentListView.as_view(), name='dealer_verification_documents'),
    # =============================================================================
    # VEHICLES
    # =============================================================================
    path('vehicle-makes/', views.VehicleMakeListView.as_view(), name='vehicle_makes'),
    path('vehicle-makes/<int:pk>/', views.VehicleMakeDetailView.as_view(), name='vehicle_make_detail'),
    
    path('vehicle-models/', views.VehicleModelListView.as_view(), name='vehicle_models'),
    
    path('vehicles/', views.VehicleListCreateView.as_view(), name='vehicles'),
    path('vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    
    # =============================================================================
    # SERVICES
    # =============================================================================
    path('service-categories/', views.ServiceCategoryListView.as_view(), name='service_categories'),
    path('service-categories/<int:pk>/', views.ServiceCategoryDetailView.as_view(), name='service_category_detail'),
    
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    # Dealer's services
    path('dealer/services/', views.DealerServiceListCreateView.as_view(), name='dealer_services'),
    path('dealer/services/<int:pk>/', views.DealerServiceDetailView.as_view(), name='dealer_service_detail'),
    
    # Service addons
    path('service-addons/', views.ServiceAddonListView.as_view(), name='service_addons'),
    
    # Technicians
    path('technicians/', views.TechnicianListView.as_view(), name='technicians'),
    path('technicians/<int:pk>/', views.TechnicianDetailView.as_view(), name='technician_detail'),
    
    # Service slots
    path('service-slots/', views.ServiceSlotListView.as_view(), name='service_slots'),
    path('dealer/slots/', views.DealerSlotListCreateView.as_view(), name='dealer_slots'),
    path('dealer/slots/<int:pk>/', views.DealerSlotDetailView.as_view(), name='dealer_slot_detail'),
    
    # =============================================================================
    # BOOKINGS
    # =============================================================================
    path('cancellation-policies/', views.CancellationPolicyListView.as_view(), name='cancellation_policies'),
    
    path('promotions/', views.PromotionListView.as_view(), name='promotions'),
    path('promotions/validate/', views.PromotionValidateView.as_view(), name='promotion_validate'),
    
    path('bookings/', views.BookingListCreateView.as_view(), name='bookings'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<int:pk>/cancel/', views.BookingCancelView.as_view(), name='booking_cancel'),
    path('bookings/<int:pk>/confirm/', views.BookingConfirmView.as_view(), name='booking_confirm'),
    
    path('booking-addons/', views.BookingAddonListView.as_view(), name='booking_addons'),
    path('booking-status-history/', views.BookingStatusHistoryListView.as_view(), name='booking_status_history'),
    
    # =============================================================================
    # PAYMENTS & PAYOUTS
    # =============================================================================
    path('virtual-cards/', views.VirtualCardListView.as_view(), name='virtual_cards'),
    
    path('payments/', views.PaymentListView.as_view(), name='payments'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    
    path('dealer/payouts/', views.DealerPayoutListView.as_view(), name='dealer_payouts'),
    path('dealer/payouts/<int:pk>/', views.DealerPayoutDetailView.as_view(), name='dealer_payout_detail'),
    
    path('balance-transactions/', views.BalanceTransactionListView.as_view(), name='balance_transactions'),
    
    # =============================================================================
    # LOYALTY & REVIEWS
    # =============================================================================
    path('loyalty-transactions/', views.LoyaltyTransactionListView.as_view(), name='loyalty_transactions'),
    
    path('reviews/', views.ReviewListCreateView.as_view(), name='reviews'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('reviews/<int:pk>/respond/', views.ReviewRespondView.as_view(), name='review_respond'),
    
    # =============================================================================
    # NOTIFICATIONS
    # =============================================================================
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_read'),
    path('notification-templates/', views.NotificationTemplateListView.as_view(), name='notification_templates'),
    
    # =============================================================================
    # SUPPORT
    # =============================================================================
    path('support/tickets/', views.SupportTicketListCreateView.as_view(), name='support_tickets'),
    path('support/tickets/<int:pk>/', views.SupportTicketDetailView.as_view(), name='support_ticket_detail'),
    path('support/messages/', views.SupportMessageListCreateView.as_view(), name='support_messages'),
    
    # =============================================================================
    # INTEGRATIONS
    # =============================================================================
    path('external-integrations/', views.ExternalIntegrationListView.as_view(), name='external_integrations'),
    path('webhook-events/', views.WebhookEventListView.as_view(), name='webhook_events'),
    path('sync-logs/', views.SyncLogListView.as_view(), name='sync_logs'),
    
    # =============================================================================
    # ANALYTICS
    # =============================================================================
    path('booking-analytics/', views.BookingAnalyticsListView.as_view(), name='booking_analytics'),
    path('dealer-analytics/', views.DealerAnalyticsListView.as_view(), name='dealer_analytics'),
    
    # =============================================================================
    # SYSTEM
    # =============================================================================
    path('system-configuration/', views.SystemConfigurationListView.as_view(), name='system_configuration'),
    path('admin-actions/', views.AdminActionListView.as_view(), name='admin_actions'),
]
