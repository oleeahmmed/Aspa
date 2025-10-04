# =============================================================================
# SIMPLIFIED CAR SERVICE BOOKING ADMIN
# =============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin

from .models import (
    CustomerProfile, DealerProfile, SubscriptionPlan, CommissionHistory,
    VehicleMake, VehicleModel, Vehicle,
    ServiceCategory, Service, Technician, ServiceSlot, ServiceAddon,
    CancellationPolicy, Promotion, Booking, BookingAddon, BookingStatusHistory,
    VirtualCard, Payment, PayoutRequest, DealerPayout, BalanceTransaction,
    LoyaltyTransaction, Review,
    ExternalIntegration, WebhookEvent, SyncLog,
    NotificationTemplate, Notification,
    DealerVerificationDocument, CustomerVerification,
    BookingAnalytics, DealerAnalytics,
    SystemConfiguration, AdminAction,
    SupportTicket, SupportMessage
)

# =============================================================================
# USER PROFILES
# =============================================================================

@admin.register(CustomerProfile)
class CustomerProfileAdmin(ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'total_bookings', 'loyalty_points']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ['name', 'price', 'commission_rate', 'max_services']
    search_fields = ['name']

@admin.register(DealerProfile)
class DealerProfileAdmin(ModelAdmin):
    list_display = [
        'business_name', 
        'user', 
        'city', 
        'is_approved', 
        'is_active', 
        'rating', 
        'total_bookings',
        # 'pretty_business_hours' # Removed
    ]
    
    list_filter = [
        'is_approved', 
        'is_active', 
        'city', 
        'business_type', 
        'subscription_plan'
    ]
    
    search_fields = [
        'business_name', 
        'user__username', 
        'business_license',
        'business_email',
        'bank_account_name'
    ]
    
    readonly_fields = [
        'rating', 
        'total_reviews', 
        'total_bookings', 
        'current_balance', 
        'api_key', 
        'created_at', 
        'updated_at'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['-is_approved', '-is_active', 'business_name']
    
    fieldsets = (
        ('User & Business Information', {
            'fields': ('user', 'business_name', 'business_license', 'business_type')
        }),
        ('Location Details', {
            'fields': ('address', 'city', 'postal_code', 'latitude', 'longitude', 'service_radius')
        }),
        ('Contact Information', {
            'fields': ('business_phone', 'business_email', 'website_url')
        }),
        ('Banking Information', {
            'fields': ('bank_account_name', 'bank_account_number', 'bank_name', 'bank_routing_number'),
            'classes': ('collapse',)
        }),
        ('Subscription & Commission', {
            'fields': ('subscription_plan', 'commission_percentage')
        }),
        ('Status & Approval', {
            'fields': ('is_approved', 'is_active')
        }),
        ('Performance Metrics (Read Only)', {
            'fields': ('rating', 'total_reviews', 'total_bookings', 'current_balance'),
            'classes': ('collapse',)
        }),
        ('External Integration', {
            'fields': ('has_external_website', 'external_api_url', 'api_key', 'webhook_url', 'webhook_secret'),
            'classes': ('collapse',)
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def pretty_business_hours(self, obj):
        """Display business hours JSON nicely in admin list view"""
        import json
        if obj.business_hours:
            return json.dumps(obj.business_hours, indent=2)
        return "-"


@admin.register(CommissionHistory)
class CommissionHistoryAdmin(ModelAdmin):
    list_display = ['dealer', 'commission_percentage', 'effective_date', 'created_at']
    search_fields = ['dealer__business_name']

# =============================================================================
# VEHICLES
# =============================================================================

@admin.register(VehicleMake)
class VehicleMakeAdmin(ModelAdmin):
    list_display = ['name', 'is_popular', 'created_at']
    search_fields = ['name']

@admin.register(VehicleModel)
class VehicleModelAdmin(ModelAdmin):
    list_display = ['name', 'make', 'year_from', 'year_to']
    search_fields = ['name', 'make__name']

@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ['license_plate', 'owner', 'make', 'model', 'year', 'is_active']
    search_fields = ['license_plate', 'vin', 'owner__username']

# =============================================================================
# SERVICES
# =============================================================================

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(ModelAdmin):
    list_display = ['name', 'estimated_duration', 'is_active']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'category', 'base_price', 'is_active']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'dealer__username']

@admin.register(Technician)
class TechnicianAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'phone_number', 'is_available']
    search_fields = ['name', 'phone_number']

@admin.register(ServiceSlot)
class ServiceSlotAdmin(ModelAdmin):
    list_display = ['service', 'date', 'start_time', 'end_time', 'available_capacity', 'is_active']
    search_fields = ['service__name']

@admin.register(ServiceAddon)
class ServiceAddonAdmin(ModelAdmin):
    list_display = ['name', 'service', 'price', 'is_active']
    search_fields = ['name']

# =============================================================================
# BOOKINGS
# =============================================================================

@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(ModelAdmin):
    list_display = ['name', 'free_cancellation_hours', 'is_active']
    search_fields = ['name']

@admin.register(Promotion)
class PromotionAdmin(ModelAdmin):
    list_display = ['code', 'title', 'promotion_type', 'discount_percentage', 'is_active']
    search_fields = ['code', 'title']

@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['booking_number', 'customer', 'status', 'total_amount', 'created_at']
    list_filter = ['status']
    search_fields = ['booking_number', 'customer__username']

@admin.register(BookingAddon)
class BookingAddonAdmin(ModelAdmin):
    list_display = ['booking', 'addon', 'quantity', 'total_price']

@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(ModelAdmin):
    list_display = ['booking', 'old_status', 'new_status', 'changed_by', 'created_at']

# =============================================================================
# PAYMENTS
# =============================================================================

@admin.register(VirtualCard)
class VirtualCardAdmin(ModelAdmin):
    list_display = ['dealer', 'last_four_digits', 'balance', 'is_active']
    search_fields = ['dealer__username']

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ['id', 'booking', 'amount', 'status', 'payment_method_type']
    list_filter = ['status']
    search_fields = ['booking__booking_number']

@admin.register(PayoutRequest)
class PayoutRequestAdmin(ModelAdmin):
    list_display = ['dealer', 'amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['dealer__username']

@admin.register(DealerPayout)
class DealerPayoutAdmin(ModelAdmin):
    list_display = ['transaction_reference', 'dealer', 'amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['transaction_reference', 'dealer__username']

@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(ModelAdmin):
    list_display = ['dealer', 'transaction_type', 'amount', 'balance_after', 'created_at']
    search_fields = ['dealer__business_name']

# =============================================================================
# LOYALTY & REVIEWS
# =============================================================================

@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(ModelAdmin):
    list_display = ['customer', 'transaction_type', 'points', 'created_at']
    search_fields = ['customer__username']

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ['customer', 'dealer', 'overall_rating', 'is_published', 'created_at']
    list_filter = ['overall_rating', 'is_published']
    search_fields = ['customer__username', 'dealer__username']

# =============================================================================
# INTEGRATIONS
# =============================================================================

@admin.register(ExternalIntegration)
class ExternalIntegrationAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'is_active', 'last_sync_at']
    search_fields = ['name', 'dealer__username']

@admin.register(WebhookEvent)
class WebhookEventAdmin(ModelAdmin):
    list_display = ['dealer', 'event_type', 'status', 'created_at']
    search_fields = ['dealer__username']

@admin.register(SyncLog)
class SyncLogAdmin(ModelAdmin):
    list_display = ['integration', 'sync_type', 'status', 'created_at']
    search_fields = ['integration__name']

# =============================================================================
# NOTIFICATIONS
# =============================================================================

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(ModelAdmin):
    list_display = ['name', 'event_type', 'is_active']
    search_fields = ['name']

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['recipient', 'title', 'channel', 'status', 'created_at']
    search_fields = ['recipient__username', 'title']

# =============================================================================
# VERIFICATION
# =============================================================================

@admin.register(DealerVerificationDocument)
class DealerVerificationDocumentAdmin(ModelAdmin):
    list_display = ['dealer', 'document_type', 'status', 'uploaded_at']
    list_filter = ['status', 'document_type']

@admin.register(CustomerVerification)
class CustomerVerificationAdmin(ModelAdmin):
    list_display = ['user', 'verification_type', 'status', 'created_at']
    list_filter = ['status', 'verification_type']

# =============================================================================
# ANALYTICS
# =============================================================================

@admin.register(BookingAnalytics)
class BookingAnalyticsAdmin(ModelAdmin):
    list_display = ['date', 'total_bookings', 'completed_bookings', 'total_revenue']

@admin.register(DealerAnalytics)
class DealerAnalyticsAdmin(ModelAdmin):
    list_display = ['dealer', 'date', 'total_bookings', 'total_earnings']

# =============================================================================
# SYSTEM
# =============================================================================

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(ModelAdmin):
    list_display = ['key', 'value', 'data_type']
    search_fields = ['key']

@admin.register(AdminAction)
class AdminActionAdmin(ModelAdmin):
    list_display = ['admin_user', 'action_type', 'created_at']
    search_fields = ['admin_user__username']

# =============================================================================
# SUPPORT
# =============================================================================

@admin.register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    list_display = ['ticket_number', 'user', 'subject', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['ticket_number', 'subject']

@admin.register(SupportMessage)
class SupportMessageAdmin(ModelAdmin):
    list_display = ['ticket', 'sender', 'created_at']
    search_fields = ['ticket__ticket_number']

# =============================================================================
# CUSTOM USER ADMIN
# =============================================================================

class SimpleUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']

admin.site.unregister(User)
admin.site.register(User, SimpleUserAdmin)

# =============================================================================
# ADMIN SITE CUSTOMIZATION
# =============================================================================

admin.site.site_header = "Car Service Booking Admin"
admin.site.site_title = "Car Service Admin"
admin.site.index_title = "Dashboard"