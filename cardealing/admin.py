# =============================================================================
# SIMPLIFIED CAR SERVICE BOOKING ADMIN
# =============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import (
    CustomerProfile, DealerProfile, SubscriptionPlan, CommissionHistory,
    VehicleMake, VehicleModel, Vehicle,
    ServiceCategory, Service, Technician, ServiceSlot, ServiceAddon, SlotTemplate,
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
    list_display = ['business_name', 'user', 'city', 'is_approved', 'is_active', 'rating']
    list_filter = ['is_approved', 'is_active', 'city']
    search_fields = ['business_name', 'user__username']

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
# SERVICES & SLOT TEMPLATES
# =============================================================================

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(ModelAdmin):
    list_display = ['name', 'estimated_duration', 'is_active']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'category', 'base_price', 'is_active', 'slot_template_actions']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'dealer__username']
    
    def slot_template_actions(self, obj):
        return format_html(
            '<div class="flex gap-1">'
            '<a class="button" href="{}" style="background: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 12px;">7 Days</a>'
            '<a class="button" href="{}" style="background: #2196F3; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 12px;">15 Days</a>'
            '<a class="button" href="{}" style="background: #FF9800; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 12px;">30 Days</a>'
            '</div>',
            f'{obj.id}/generate_all_slots/7/',
            f'{obj.id}/generate_all_slots/15/',
            f'{obj.id}/generate_all_slots/30/'
        )
    slot_template_actions.short_description = 'Generate Slots'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate_all_slots/<int:days>/', 
                 self.admin_site.admin_view(self.generate_all_slots_view),
                 name='service_generate_all_slots'),
        ]
        return custom_urls + urls
    
    def generate_all_slots_view(self, request, object_id, days):
        from .models import generate_all_slots_for_service
        service = Service.objects.get(id=object_id)
        
        generated_slots = generate_all_slots_for_service(service, days)
        
        self.message_user(
            request, 
            f"Successfully generated {len(generated_slots)} slots from all templates for {days} days",
            messages.SUCCESS
        )
        
        return HttpResponseRedirect('../../')

@admin.register(Technician)
class TechnicianAdmin(ModelAdmin):
    list_display = ['name', 'dealer', 'phone_number', 'is_available']
    search_fields = ['name', 'phone_number']

@admin.register(SlotTemplate)
class SlotTemplateAdmin(ModelAdmin):
    list_display = ['name', 'service', 'day_of_week', 'start_time', 'end_time', 'is_active', 'batch_actions']
    list_filter = ['is_active', 'day_of_week', 'service__dealer']
    search_fields = ['name', 'service__name']
    
    def batch_actions(self, obj):
        return format_html(
            '<div class="flex gap-1">'
            '<a class="button" href="{}" style="background: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 12px;">7 Days</a>'
            '<a class="button" href="{}" style="background: #2196F3; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 12px;">15 Days</a>'
            '<a class="button" href="{}" style="background: #FF9800; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 12px;">30 Days</a>'
            '</div>',
            f'{obj.id}/generate_slots/7/',
            f'{obj.id}/generate_slots/15/',
            f'{obj.id}/generate_slots/30/'
        )
    batch_actions.short_description = 'Generate Slots'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate_slots/<int:days>/', 
                 self.admin_site.admin_view(self.generate_slots_view),
                 name='slot_template_generate_slots'),
        ]
        return custom_urls + urls
    
    def generate_slots_view(self, request, object_id, days):
        slot_template = SlotTemplate.objects.get(id=object_id)
        
        if days == 7:
            generated_slots = slot_template.generate_slots_7_days()
        elif days == 15:
            generated_slots = slot_template.generate_slots_15_days()
        elif days == 30:
            generated_slots = slot_template.generate_slots_30_days()
        else:
            generated_slots = slot_template.generate_slots_for_days(days)
        
        self.message_user(
            request, 
            f"Successfully generated {len(generated_slots)} slots for {days} days from template '{slot_template.name}'",
            messages.SUCCESS
        )
        
        return HttpResponseRedirect('../../')

@admin.register(ServiceSlot)
class ServiceSlotAdmin(ModelAdmin):
    list_display = ['service', 'date', 'start_time', 'end_time', 'available_capacity', 'is_active', 'slot_source']
    list_filter = ['is_active', 'is_generated_from_template', 'date']
    search_fields = ['service__name']
    
    def slot_source(self, obj):
        if obj.is_generated_from_template:
            return format_html(
                '<span style="color: #4CAF50; font-weight: bold;">Template</span>'
            )
        return format_html(
            '<span style="color: #2196F3; font-weight: bold;">Manual</span>'
        )
    slot_source.short_description = 'Source'

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