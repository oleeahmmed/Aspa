# =============================================================================
# CAR SERVICE BOOKING SYSTEM - COMPLETE DJANGO ADMIN WITH UNFOLD
# =============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.filters.admin import (
    RangeDateFilter, RangeDateTimeFilter, RelatedDropdownFilter, 
    ChoicesDropdownFilter, MultipleRelatedDropdownFilter
)
from unfold.decorators import display
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget

from .models import (
    # User Profiles
    CustomerProfile, DealerProfile, SubscriptionPlan, CommissionHistory,
    
    # Vehicle Management
    VehicleMake, VehicleModel, Vehicle,
    
    # Service Management
    ServiceCategory, Service, Technician, ServiceSlot, ServiceAddon,
    
    # Booking System
    CancellationPolicy, Promotion, Booking, BookingAddon, BookingStatusHistory,
    
    # Payment System
    VirtualCard, Payment, PayoutRequest, DealerPayout, BalanceTransaction,
    
    # Loyalty System
    LoyaltyTransaction,
    
    # Reviews & Ratings
    Review,
    
    # External Integration
    ExternalIntegration, WebhookEvent, SyncLog,
    
    # Notifications
    NotificationTemplate, Notification,
    
    # Verification System
    DealerVerificationDocument, CustomerVerification,
    
    # Analytics
    BookingAnalytics, DealerAnalytics,
    
    # System Configuration
    SystemConfiguration, AdminAction,
    
    # Support System
    SupportTicket, SupportMessage
)

# =============================================================================
# INLINE ADMIN CLASSES
# =============================================================================

class CommissionHistoryInline(TabularInline):
    model = CommissionHistory
    extra = 0
    readonly_fields = ['created_at']
    fields = ['commission_percentage', 'effective_date', 'reason', 'created_by', 'created_at']

class VehicleInline(TabularInline):
    model = Vehicle
    extra = 0
    fields = ['make', 'model', 'year', 'license_plate', 'is_primary', 'is_active']
    readonly_fields = ['created_at']

class TechnicianInline(TabularInline):
    model = Technician
    extra = 0
    fields = ['name', 'phone_number', 'is_available']

class ServiceSlotInline(TabularInline):
    model = ServiceSlot
    extra = 0
    fields = ['date', 'start_time', 'end_time', 'total_capacity', 'available_capacity', 'is_active']
    readonly_fields = ['created_at']

class ServiceAddonInline(TabularInline):
    model = ServiceAddon
    extra = 0
    fields = ['name', 'price', 'is_required', 'is_active']

class BookingAddonInline(TabularInline):
    model = BookingAddon
    extra = 0
    fields = ['addon', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']

class BookingStatusHistoryInline(TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'created_at']
    fields = ['old_status', 'new_status', 'changed_by', 'reason', 'created_at']

class DealerVerificationDocumentInline(StackedInline):
    model = DealerVerificationDocument
    extra = 0
    fields = ['document_type', 'document_file', 'status', 'admin_notes', 'reviewed_by', 'reviewed_at']
    readonly_fields = ['uploaded_at']

class SupportMessageInline(TabularInline):
    model = SupportMessage
    extra = 0
    fields = ['sender', 'message', 'attachment', 'is_read', 'created_at']
    readonly_fields = ['sender', 'created_at']

class BalanceTransactionInline(TabularInline):
    model = BalanceTransaction
    extra = 0
    readonly_fields = ['created_at', 'balance_before', 'balance_after']
    fields = ['transaction_type', 'amount', 'description', 'balance_before', 'balance_after', 'created_at']

# =============================================================================
# USER PROFILE ADMIN CLASSES
# =============================================================================

@admin.register(CustomerProfile)
class CustomerProfileAdmin(ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'total_bookings', 'total_spent', 'loyalty_points', 'created_at']
    list_filter = [
        ('created_at', RangeDateFilter),
        'city',
        'preferred_notification',
        ('total_bookings'),
    ]
    search_fields = ['user__username', 'user__email', 'phone_number', 'city']
    readonly_fields = ['total_bookings', 'total_spent', 'loyalty_points', 'created_at', 'updated_at']
    
    fieldsets = [
        ('User Information', {
            'fields': ['user']
        }),
        ('Personal Details', {
            'fields': ['date_of_birth', 'phone_number', 'emergency_contact']
        }),
        ('Address Information', {
            'fields': ['address', 'city', 'postal_code', 'latitude', 'longitude']
        }),
        ('Preferences', {
            'fields': ['preferred_notification']
        }),
        ('Customer Metrics', {
            'fields': ['total_bookings', 'total_spent', 'loyalty_points'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ['name', 'price', 'commission_rate', 'max_services', 'featured_listing', 'priority_support', 'created_at']
    list_filter = ['featured_listing', 'priority_support', 'analytics_access', 'api_access']
    search_fields = ['name']
    
    fieldsets = [
        ('Plan Details', {
            'fields': ['name', 'price', 'commission_rate']
        }),
        ('Features', {
            'fields': ['max_services', 'featured_listing', 'priority_support', 'analytics_access', 'api_access']
        }),
        ('Additional Configuration', {
            'fields': ['features'],
            'classes': ['collapse']
        }),
    ]

@admin.register(DealerProfile)
class DealerProfileAdmin(ModelAdmin):
    list_display = ['business_name', 'user', 'business_type', 'city', 'is_approved', 'is_active', 'rating', 'current_balance']
    list_filter = [
        'is_approved',
        'is_active',
        'business_type',
        'city',
        ('created_at', RangeDateFilter),
        ('subscription_plan', RelatedDropdownFilter),
    ]
    search_fields = ['business_name', 'user__username', 'business_license', 'city']
    readonly_fields = ['rating', 'total_reviews', 'total_bookings', 'current_balance', 'api_key', 'created_at', 'updated_at']
    
    actions = ['approve_dealers', 'deactivate_dealers', 'activate_dealers']
    
    fieldsets = [
        ('User & Business Information', {
            'fields': ['user', 'business_name', 'business_license', 'business_type']
        }),
        ('Location Details', {
            'fields': ['address', 'city', 'postal_code', 'latitude', 'longitude', 'service_radius']
        }),
        ('Contact Information', {
            'fields': ['business_phone', 'business_email', 'website_url']
        }),
        ('Financial Information', {
            'fields': ['bank_account_name', 'bank_account_number', 'bank_name', 'bank_routing_number']
        }),
        ('Commission & Subscription', {
            'fields': ['commission_percentage', 'subscription_plan']
        }),
        ('Status & Performance', {
            'fields': ['is_approved', 'is_active', 'rating', 'total_reviews', 'total_bookings', 'current_balance'],
            'classes': ['collapse']
        }),
        ('Business Hours', {
            'fields': ['business_hours'],
            'classes': ['collapse']
        }),
        ('External Integration', {
            'fields': ['has_external_website', 'external_api_url', 'api_key', 'webhook_url', 'webhook_secret'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [CommissionHistoryInline, TechnicianInline, DealerVerificationDocumentInline, BalanceTransactionInline]
    
    @admin.action(description='Approve selected dealers')
    def approve_dealers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} dealers were approved successfully.')
    
    @admin.action(description='Deactivate selected dealers')
    def deactivate_dealers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} dealers were deactivated successfully.')
    
    @admin.action(description='Activate selected dealers')
    def activate_dealers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} dealers were activated successfully.')

# =============================================================================
# VEHICLE MANAGEMENT ADMIN CLASSES
# =============================================================================

@admin.register(VehicleMake)
class VehicleMakeAdmin(ModelAdmin):
    list_display = ['name', 'is_popular', 'model_count', 'created_at']
    list_filter = ['is_popular', ('created_at', RangeDateFilter)]
    search_fields = ['name']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(model_count=Count('models'))
    
    @display(description='Model Count')
    def model_count(self, obj):
        return obj.model_count

@admin.register(VehicleModel)
class VehicleModelAdmin(ModelAdmin):
    list_display = ['name', 'make', 'year_from', 'year_to', 'created_at']
    list_filter = [
        ('make', RelatedDropdownFilter),
        'year_from',
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['name', 'make__name']
    
    fieldsets = [
        ('Model Information', {
            'fields': ['make', 'name']
        }),
        ('Production Years', {
            'fields': ['year_from', 'year_to']
        }),
    ]

@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ['license_plate', 'owner', 'make', 'model', 'year', 'fuel_type', 'is_primary', 'is_active']
    list_filter = [
        ('make', RelatedDropdownFilter),
        ('model', RelatedDropdownFilter),
        'fuel_type',
        'transmission',
        'is_primary',
        'is_active',
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['license_plate', 'vin', 'owner__username', 'make__name', 'model__name']
    
    fieldsets = [
        ('Owner Information', {
            'fields': ['owner']
        }),
        ('Vehicle Details', {
            'fields': ['make', 'model', 'year', 'color', 'license_plate', 'vin']
        }),
        ('Technical Specifications', {
            'fields': ['fuel_type', 'transmission', 'engine_cc', 'current_mileage']
        }),
        ('Status', {
            'fields': ['is_primary', 'is_active']
        }),
        ('Service History', {
            'fields': ['last_service_date', 'next_service_due'],
            'classes': ['collapse']
        }),
    ]

# =============================================================================
# SERVICE MANAGEMENT ADMIN CLASSES
# =============================================================================

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(ModelAdmin):
    list_display = ['name', 'parent', 'estimated_duration', 'requires_vehicle_drop', 'sort_order', 'is_active']
    list_filter = ['is_active', 'requires_vehicle_drop', ('parent', RelatedDropdownFilter)]
    search_fields = ['name', 'description']
    
    fieldsets = [
        ('Category Information', {
            'fields': ['name', 'description', 'icon', 'parent']
        }),
        ('Service Attributes', {
            'fields': ['estimated_duration', 'requires_vehicle_drop']
        }),
        ('Display Settings', {
            'fields': ['sort_order', 'is_active']
        }),
    ]

@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'category', 'base_price', 'discounted_price', 'estimated_duration', 'is_active', 'is_featured']
    list_filter = [
        ('dealer', RelatedDropdownFilter),
        ('category', RelatedDropdownFilter),
        'service_location',
        'is_active',
        'is_featured',
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['name', 'description', 'dealer__username']
    filter_horizontal = ['supported_makes']
    
    fieldsets = [
        ('Service Information', {
            'fields': ['dealer', 'category', 'name', 'description', 'short_description']
        }),
        ('Pricing', {
            'fields': ['base_price', 'discounted_price']
        }),
        ('Service Configuration', {
            'fields': ['estimated_duration', 'max_concurrent_slots', 'service_location']
        }),
        ('Vehicle Support', {
            'fields': ['supported_makes', 'supported_fuel_types', 'min_year', 'max_year']
        }),
        ('Business Rules', {
            'fields': ['advance_booking_hours', 'cancellation_hours']
        }),
        ('Features', {
            'fields': ['includes', 'requirements'],
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ['is_active', 'is_featured']
        }),
        ('External Integration', {
            'fields': ['external_service_id', 'sync_with_external'],
            'classes': ['collapse']
        }),
        ('Analytics', {
            'fields': ['total_bookings', 'view_count'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['total_bookings', 'view_count']
    inlines = [ServiceSlotInline, ServiceAddonInline]

@admin.register(Technician)
class TechnicianAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'phone_number', 'is_available', 'created_at']
    list_filter = [
        ('dealer', RelatedDropdownFilter),
        'is_available',
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['name', 'phone_number', 'dealer__business_name']

@admin.register(ServiceSlot)
class ServiceSlotAdmin(ModelAdmin):
    list_display = ['service', 'date', 'start_time', 'end_time', 'total_capacity', 'available_capacity', 'assigned_technician', 'is_active']
    list_filter = [
        ('service', RelatedDropdownFilter),
        ('date', RangeDateFilter),
        ('assigned_technician', RelatedDropdownFilter),
        'is_active',
        'is_blocked'
    ]
    search_fields = ['service__name', 'service__dealer__username']
    
    fieldsets = [
        ('Slot Information', {
            'fields': ['service', 'date', 'start_time', 'end_time']
        }),
        ('Capacity Management', {
            'fields': ['total_capacity', 'available_capacity', 'custom_price']
        }),
        ('Assignment', {
            'fields': ['assigned_technician']
        }),
        ('Status', {
            'fields': ['is_active', 'is_blocked', 'block_reason']
        }),
        ('External Integration', {
            'fields': ['external_slot_id', 'sync_with_external'],
            'classes': ['collapse']
        }),
    ]

# =============================================================================
# BOOKING SYSTEM ADMIN CLASSES
# =============================================================================

@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(ModelAdmin):
    list_display = ['name', 'free_cancellation_hours', 'partial_refund_percentage', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Promotion)
class PromotionAdmin(ModelAdmin):
    list_display = ['code', 'title', 'promotion_type', 'discount_percentage', 'start_date', 'end_date', 'current_uses', 'is_active']
    list_filter = [
        'promotion_type',
        'target_audience',
        ('start_date', RangeDateFilter),
        ('end_date', RangeDateFilter),
        'is_active'
    ]
    search_fields = ['code', 'title', 'description']
    filter_horizontal = ['applicable_services', 'applicable_categories']
    
    fieldsets = [
        ('Promotion Information', {
            'fields': ['code', 'title', 'description', 'promotion_type']
        }),
        ('Discount Values', {
            'fields': ['discount_percentage', 'discount_amount', 'bonus_points']
        }),
        ('Targeting', {
            'fields': ['target_audience', 'applicable_services', 'applicable_categories', 'minimum_order_amount']
        }),
        ('Validity', {
            'fields': ['start_date', 'end_date', 'max_uses', 'max_uses_per_user', 'current_uses']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
    ]

@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['booking_number', 'customer', 'service_name', 'status', 'total_amount', 'service_scheduled_at', 'created_at']
    list_filter = [
        ('status', ChoicesDropdownFilter),
        ('customer', RelatedDropdownFilter),
        'service_location',
        'booking_for',
        'source',
        ('service_scheduled_at', RangeDateTimeFilter),
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['booking_number', 'customer__username', 'service_slot__service__name']
    readonly_fields = ['booking_number', 'dealer_amount', 'platform_fee', 'created_at', 'updated_at']
    
    actions = ['confirm_bookings', 'cancel_bookings']
    
    fieldsets = [
        ('Booking Information', {
            'fields': ['booking_number', 'customer', 'service_slot', 'vehicle', 'promotion']
        }),
        ('Booking Details', {
            'fields': ['booking_for', 'contact_name', 'contact_phone', 'friend_vehicle_info']
        }),
        ('Service Location', {
            'fields': ['service_location', 'customer_address']
        }),
        ('Status & Source', {
            'fields': ['status', 'source']
        }),
        ('Financial Details', {
            'fields': ['service_amount', 'discount_amount', 'tax_amount', 'total_amount', 'platform_fee', 'dealer_amount']
        }),
        ('Policies', {
            'fields': ['cancellation_policy']
        }),
        ('Timing', {
            'fields': ['booking_deadline', 'service_scheduled_at', 'service_started_at', 'service_completed_at']
        }),
        ('Communication', {
            'fields': ['special_instructions', 'cancellation_reason']
        }),
        ('External Integration', {
            'fields': ['external_booking_id', 'payment_intent_id'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [BookingAddonInline, BookingStatusHistoryInline]
    
    @display(description='Service Name')
    def service_name(self, obj):
        return obj.service_slot.service.name
    
    @admin.action(description='Confirm selected bookings')
    def confirm_bookings(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{updated} bookings were confirmed successfully.')
    
    @admin.action(description='Cancel selected bookings')
    def cancel_bookings(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled_by_dealer')
        self.message_user(request, f'{updated} bookings were cancelled successfully.')

# =============================================================================
# PAYMENT SYSTEM ADMIN CLASSES
# =============================================================================

@admin.register(VirtualCard)
class VirtualCardAdmin(ModelAdmin):
    list_display = ['dealer', 'last_four_digits', 'balance', 'is_active', 'created_at']
    list_filter = ['is_active', ('created_at', RangeDateFilter)]
    search_fields = ['dealer__username', 'card_number']
    readonly_fields = ['card_number', 'last_four_digits', 'created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ['id', 'booking_number', 'amount', 'status', 'payment_method_type', 'created_at']
    list_filter = [
        ('status', ChoicesDropdownFilter),
        'payment_method_type',
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['booking__booking_number', 'stripe_payment_intent_id', 'stripe_charge_id']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_charge_id', 'gateway_response', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Payment Information', {
            'fields': ['booking', 'amount', 'currency', 'status']
        }),
        ('Payment Method', {
            'fields': ['payment_method_type', 'payment_method_details', 'virtual_card']
        }),
        ('Stripe Integration', {
            'fields': ['stripe_payment_intent_id', 'stripe_charge_id'],
            'classes': ['collapse']
        }),
        ('Gateway Response', {
            'fields': ['gateway_response'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['authorized_at', 'captured_at', 'failed_at', 'created_at', 'updated_at']
        }),
        ('Refund Information', {
            'fields': ['refund_amount', 'refunded_at']
        }),
        ('Error Handling', {
            'fields': ['failure_code', 'failure_message'],
            'classes': ['collapse']
        }),
    ]
    
    @display(description='Booking Number')
    def booking_number(self, obj):
        return obj.booking.booking_number

@admin.register(DealerPayout)
class DealerPayoutAdmin(ModelAdmin):
    list_display = ['transaction_reference', 'dealer', 'amount', 'net_amount', 'status', 'created_at']
    list_filter = [
        ('status', ChoicesDropdownFilter),
        ('dealer', RelatedDropdownFilter),
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['transaction_reference', 'dealer__username']
    readonly_fields = ['transaction_reference', 'net_amount', 'created_at', 'updated_at']
    filter_horizontal = ['related_bookings']
    
    actions = ['approve_payouts', 'process_payouts']
    
    fieldsets = [
        ('Payout Information', {
            'fields': ['dealer', 'amount', 'processing_fee', 'net_amount']
        }),
        ('Status', {
            'fields': ['status', 'transaction_reference']
        }),
        ('Banking Details', {
            'fields': ['bank_details']
        }),
        ('Processing Information', {
            'fields': ['processed_by', 'admin_notes', 'processed_at']
        }),
        ('Related Bookings', {
            'fields': ['related_bookings'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    @admin.action(description='Approve selected payouts')
    def approve_payouts(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f'{updated} payouts were approved successfully.')
    
    @admin.action(description='Process selected payouts')
    def process_payouts(self, request, queryset):
        updated = queryset.filter(status='approved').update(status='processing')
        self.message_user(request, f'{updated} payouts are now being processed.')

# =============================================================================
# LOYALTY & REVIEW SYSTEM ADMIN CLASSES
# =============================================================================

@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(ModelAdmin):
    list_display = ['customer', 'transaction_type', 'points', 'balance_after', 'created_at']
    list_filter = [
        ('transaction_type', ChoicesDropdownFilter),
        ('customer', RelatedDropdownFilter),
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['customer__username', 'description']
    readonly_fields = ['balance_before', 'balance_after', 'created_at']

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ['customer', 'dealer', 'overall_rating', 'title', 'is_published', 'is_verified', 'created_at']
    list_filter = [
        'overall_rating',
        'is_published',
        'is_verified',
        ('dealer', RelatedDropdownFilter),
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['customer__username', 'dealer__username', 'title', 'comment']
    readonly_fields = ['booking', 'created_at']
    
    actions = ['publish_reviews', 'verify_reviews']
    
    fieldsets = [
        ('Review Information', {
            'fields': ['customer', 'dealer', 'booking']
        }),
        ('Ratings', {
            'fields': ['overall_rating', 'service_quality', 'punctuality', 'value_for_money']
        }),
        ('Review Content', {
            'fields': ['title', 'comment', 'photos']
        }),
        ('Status', {
            'fields': ['is_published', 'is_verified']
        }),
        ('Dealer Response', {
            'fields': ['dealer_response', 'dealer_response_date'],
            'classes': ['collapse']
        }),
    ]
    
    @admin.action(description='Publish selected reviews')
    def publish_reviews(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} reviews were published successfully.')
    
    @admin.action(description='Verify selected reviews')
    def verify_reviews(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} reviews were verified successfully.')

# =============================================================================
# EXTERNAL INTEGRATION ADMIN CLASSES
# =============================================================================

@admin.register(ExternalIntegration)
class ExternalIntegrationAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'sync_services', 'sync_slots', 'sync_bookings', 'is_active', 'last_sync_at']
    list_filter = [
        ('dealer', RelatedDropdownFilter),
        'sync_services',
        'sync_slots',
        'sync_bookings',
        'is_active',
        ('last_sync_at', RangeDateTimeFilter)
    ]
    search_fields = ['name', 'dealer__username', 'api_endpoint']
    
    fieldsets = [
        ('Integration Information', {
            'fields': ['dealer', 'name', 'api_endpoint', 'api_key', 'webhook_url']
        }),
        ('Configuration', {
            'fields': ['sync_services', 'sync_slots', 'sync_bookings']
        }),
        ('Status', {
            'fields': ['is_active', 'last_sync_at', 'last_sync_status']
        }),
    ]

@admin.register(WebhookEvent)
class WebhookEventAdmin(ModelAdmin):
    list_display = ['dealer', 'event_type', 'status', 'retry_count', 'created_at', 'processed_at']
    list_filter = [
        ('dealer', RelatedDropdownFilter),
        ('event_type', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['dealer__username', 'external_id']
    readonly_fields = ['created_at', 'processed_at']

# =============================================================================
# NOTIFICATION SYSTEM ADMIN CLASSES
# =============================================================================

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(ModelAdmin):
    list_display = ['name', 'event_type', 'is_active', 'created_at']
    list_filter = [
        ('event_type', ChoicesDropdownFilter),
        'is_active',
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['name', 'email_subject', 'event_type']
    
    fieldsets = [
        ('Template Information', {
            'fields': ['name', 'event_type', 'is_active']
        }),
        ('Email Template', {
            'fields': ['email_subject', 'email_body']
        }),
        ('SMS Template', {
            'fields': ['sms_message']
        }),
        ('Push Notification Template', {
            'fields': ['push_title', 'push_body']
        }),
    ]

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['recipient', 'title', 'channel', 'status', 'sent_at', 'read_at', 'created_at']
    list_filter = [
        ('recipient', RelatedDropdownFilter),
        ('channel', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('created_at', RangeDateTimeFilter),
        ('sent_at', RangeDateTimeFilter)
    ]
    search_fields = ['recipient__username', 'title', 'message']
    readonly_fields = ['sent_at', 'read_at', 'created_at']
    
    actions = ['mark_as_sent', 'resend_notifications']
    
    fieldsets = [
        ('Notification Information', {
            'fields': ['recipient', 'template', 'title', 'message']
        }),
        ('Channel & Status', {
            'fields': ['channel', 'status']
        }),
        ('Related Objects', {
            'fields': ['related_booking'],
            'classes': ['collapse']
        }),
        ('Delivery Tracking', {
            'fields': ['sent_at', 'read_at', 'created_at']
        }),
    ]
    
    @admin.action(description='Mark selected notifications as sent')
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(status='sent', sent_at=timezone.now())
        self.message_user(request, f'{updated} notifications were marked as sent.')
    
    @admin.action(description='Resend selected notifications')
    def resend_notifications(self, request, queryset):
        updated = queryset.filter(status='failed').update(status='pending')
        self.message_user(request, f'{updated} notifications were queued for resending.')

# =============================================================================
# VERIFICATION SYSTEM ADMIN CLASSES
# =============================================================================

@admin.register(DealerVerificationDocument)
class DealerVerificationDocumentAdmin(ModelAdmin):
    list_display = ['dealer_name', 'document_type', 'status', 'uploaded_at', 'reviewed_by', 'reviewed_at']
    list_filter = [
        ('document_type', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('uploaded_at', RangeDateFilter),
        ('reviewed_by', RelatedDropdownFilter)
    ]
    search_fields = ['dealer__business_name', 'dealer__user__username']
    readonly_fields = ['uploaded_at']
    
    actions = ['approve_documents', 'reject_documents']
    
    fieldsets = [
        ('Document Information', {
            'fields': ['dealer', 'document_type', 'document_file']
        }),
        ('Review Status', {
            'fields': ['status', 'admin_notes', 'reviewed_by', 'reviewed_at']
        }),
        ('Timestamps', {
            'fields': ['uploaded_at']
        }),
    ]
    
    @display(description='Dealer Name')
    def dealer_name(self, obj):
        return obj.dealer.business_name
    
    @admin.action(description='Approve selected documents')
    def approve_documents(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='approved', 
            reviewed_by=request.user, 
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} documents were approved successfully.')
    
    @admin.action(description='Reject selected documents')
    def reject_documents(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='rejected', 
            reviewed_by=request.user, 
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} documents were rejected.')

@admin.register(CustomerVerification)
class CustomerVerificationAdmin(ModelAdmin):
    list_display = ['user', 'verification_type', 'status', 'created_at', 'updated_at']
    list_filter = [
        ('verification_type', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['token', 'created_at', 'updated_at']

# =============================================================================
# ANALYTICS & REPORTING ADMIN CLASSES
# =============================================================================

@admin.register(BookingAnalytics)
class BookingAnalyticsAdmin(ModelAdmin):
    list_display = ['date', 'total_bookings', 'completed_bookings', 'cancelled_bookings', 'total_revenue', 'new_customers']
    list_filter = [('date', RangeDateFilter)]
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Date', {
            'fields': ['date']
        }),
        ('Booking Metrics', {
            'fields': ['total_bookings', 'confirmed_bookings', 'completed_bookings', 'cancelled_bookings', 'no_show_bookings']
        }),
        ('Financial Metrics', {
            'fields': ['total_revenue', 'platform_fees', 'dealer_payouts']
        }),
        ('Customer Metrics', {
            'fields': ['new_customers', 'returning_customers']
        }),
    ]
    
    def has_add_permission(self, request):
        return False  # Analytics should be generated automatically
    
    def has_delete_permission(self, request, obj=None):
        return False  # Don't allow deletion of analytics data

@admin.register(DealerAnalytics)
class DealerAnalyticsAdmin(ModelAdmin):
    list_display = ['dealer', 'date', 'total_bookings', 'completed_bookings', 'total_earnings', 'average_rating']
    list_filter = [
        ('dealer', RelatedDropdownFilter),
        ('date', RangeDateFilter)
    ]
    search_fields = ['dealer__username']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Analytics Information', {
            'fields': ['dealer', 'date']
        }),
        ('Performance Metrics', {
            'fields': ['total_bookings', 'completed_bookings', 'cancelled_bookings', 'no_show_bookings']
        }),
        ('Financial Metrics', {
            'fields': ['total_earnings', 'platform_fees_paid']
        }),
        ('Service Metrics', {
            'fields': ['average_rating', 'new_reviews']
        }),
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# =============================================================================
# SYSTEM CONFIGURATION & ADMIN TRACKING ADMIN CLASSES
# =============================================================================

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(ModelAdmin):
    list_display = ['key', 'value_preview', 'data_type', 'updated_at']
    list_filter = ['data_type', ('updated_at', RangeDateFilter)]
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Configuration', {
            'fields': ['key', 'value', 'data_type']
        }),
        ('Description', {
            'fields': ['description']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    @display(description='Value Preview')
    def value_preview(self, obj):
        if len(obj.value) > 50:
            return f"{obj.value[:50]}..."
        return obj.value

@admin.register(AdminAction)
class AdminActionAdmin(ModelAdmin):
    list_display = ['admin_user', 'action_type', 'target_model', 'target_id', 'created_at']
    list_filter = [
        ('admin_user', RelatedDropdownFilter),
        ('action_type', ChoicesDropdownFilter),
        'target_model',
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['admin_user__username', 'description']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Admin actions should be logged automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Admin actions should not be editable
    
    def has_delete_permission(self, request, obj=None):
        return False  # Admin actions should not be deletable

# =============================================================================
# SUPPORT SYSTEM ADMIN CLASSES
# =============================================================================

@admin.register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    list_display = ['ticket_number', 'user', 'subject', 'category', 'status', 'priority', 'assigned_to', 'created_at']
    list_filter = [
        ('category', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('priority', ChoicesDropdownFilter),
        ('assigned_to', RelatedDropdownFilter),
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['ticket_number', 'user__username', 'subject', 'description']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']
    
    actions = ['assign_to_me', 'mark_as_resolved', 'mark_as_closed']
    
    fieldsets = [
        ('Ticket Information', {
            'fields': ['ticket_number', 'user', 'subject', 'description']
        }),
        ('Classification', {
            'fields': ['category', 'priority']
        }),
        ('Status & Assignment', {
            'fields': ['status', 'assigned_to']
        }),
        ('Related Objects', {
            'fields': ['related_booking'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at', 'resolved_at']
        }),
    ]
    
    inlines = [SupportMessageInline]
    
    @admin.action(description='Assign selected tickets to me')
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user, status='in_progress')
        self.message_user(request, f'{updated} tickets were assigned to you.')
    
    @admin.action(description='Mark selected tickets as resolved')
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} tickets were marked as resolved.')
    
    @admin.action(description='Mark selected tickets as closed')
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} tickets were closed.')

@admin.register(SupportMessage)
class SupportMessageAdmin(ModelAdmin):
    list_display = ['ticket', 'sender', 'message_preview', 'is_read', 'created_at']
    list_filter = [
        ('ticket', RelatedDropdownFilter),
        ('sender', RelatedDropdownFilter),
        'is_read',
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['ticket__ticket_number', 'sender__username', 'message']
    readonly_fields = ['created_at']
    
    @display(description='Message Preview')
    def message_preview(self, obj):
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message

# =============================================================================
# ADDITIONAL MODEL ADMIN CLASSES
# =============================================================================

@admin.register(ServiceAddon)
class ServiceAddonAdmin(ModelAdmin):
    list_display = ['name', 'service', 'price', 'is_required', 'is_active', 'created_at']
    list_filter = [
        ('service', RelatedDropdownFilter),
        'is_required',
        'is_active',
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['name', 'description', 'service__name']

@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(ModelAdmin):
    list_display = ['booking', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = [
        ('booking', RelatedDropdownFilter),
        'old_status',
        'new_status',
        ('changed_by', RelatedDropdownFilter),
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['booking__booking_number', 'reason']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Status history should be created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Status history should not be editable
    
    def has_delete_permission(self, request, obj=None):
        return False  # Status history should not be deletable

@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(ModelAdmin):
    list_display = ['dealer', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = [
        ('dealer', RelatedDropdownFilter),
        ('transaction_type', ChoicesDropdownFilter),
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['dealer__business_name', 'description']
    readonly_fields = ['balance_before', 'balance_after', 'created_at']
    
    def has_add_permission(self, request):
        return False  # Balance transactions should be created automatically

@admin.register(SyncLog)
class SyncLogAdmin(ModelAdmin):
    list_display = ['integration', 'sync_type', 'status', 'records_processed', 'execution_time_ms', 'created_at']
    list_filter = [
        ('integration', RelatedDropdownFilter),
        ('sync_type', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('created_at', RangeDateTimeFilter)
    ]
    search_fields = ['integration__name']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Sync Information', {
            'fields': ['integration', 'sync_type', 'status']
        }),
        ('Data', {
            'fields': ['request_data', 'response_data', 'error_message'],
            'classes': ['collapse']
        }),
        ('Metrics', {
            'fields': ['records_processed', 'execution_time_ms', 'created_at']
        }),
    ]
    
    def has_add_permission(self, request):
        return False

# =============================================================================
# CUSTOM USER ADMIN (EXTENDING DEFAULT)
# =============================================================================

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'user_type']
    
    @display(description='User Type')
    def user_type(self, obj):
        if hasattr(obj, 'customer_profile'):
            return 'Customer'
        elif hasattr(obj, 'dealer_profile'):
            return 'Dealer'
        elif obj.is_staff:
            return 'Admin'
        return 'Unknown'

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# =============================================================================
# ADMIN SITE CUSTOMIZATION
# =============================================================================

# Customize admin site headers and titles
admin.site.site_header = "Car Service Booking Admin"
admin.site.site_title = "Car Service Admin"
admin.site.index_title = "Welcome to Car Service Booking Administration"

# =============================================================================
# CUSTOM ADMIN DASHBOARD (Optional - requires custom template)
# =============================================================================

class AdminDashboardView:
    """
    Custom dashboard view for admin overview.
    This would require creating custom templates and views.
    """
    
    @staticmethod
    def get_dashboard_stats():
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        stats = {
            'total_bookings': Booking.objects.count(),
            'total_customers': CustomerProfile.objects.count(),
            'total_dealers': DealerProfile.objects.count(),
            'total_services': Service.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'active_dealers': DealerProfile.objects.filter(is_active=True, is_approved=True).count(),
            'recent_bookings': Booking.objects.filter(created_at__gte=last_30_days).count(),
            'total_revenue': Payment.objects.filter(status='succeeded').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'pending_payouts': DealerPayout.objects.filter(status='pending').count(),
            'open_tickets': SupportTicket.objects.filter(status='open').count(),
        }
        
        return stats

# =============================================================================
# BULK ACTIONS AND UTILITIES
# =============================================================================

def bulk_approve_dealers(modeladmin, request, queryset):
    """Bulk approve dealers"""
    queryset.update(is_approved=True)

def bulk_send_notifications(modeladmin, request, queryset):
    """Bulk send notifications"""
    from django.utils import timezone
    queryset.filter(status='pending').update(status='sent', sent_at=timezone.now())

# =============================================================================
# FORM CUSTOMIZATIONS (Optional)
# =============================================================================

from django import forms

class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'
        widgets = {
            'special_instructions': forms.Textarea(attrs={'rows': 3}),
            'cancellation_reason': forms.Textarea(attrs={'rows': 3}),
        }

class DealerProfileAdminForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'business_hours': forms.Textarea(attrs={'rows': 5}),
        }

# Update the admin classes to use custom forms
# (Add form = BookingAdminForm to BookingAdmin class)
# (Add form = DealerProfileAdminForm to DealerProfileAdmin class)