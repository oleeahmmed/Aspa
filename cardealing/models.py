# =============================================================================
# CAR SERVICE BOOKING SYSTEM - COMPLETE MODELS
# =============================================================================

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import uuid
import secrets
from decimal import Decimal



# =============================================================================
# 1. ENHANCED USER PROFILES
# =============================================================================

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$', 'Invalid phone number format')]
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$', 'Invalid phone number format')]
    )
    
    # Location for service requests
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Preferences
    preferred_notification = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('sms', 'SMS'), ('both', 'Both')],
        default='email'
    )
    
    # Customer metrics
    total_bookings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loyalty_points = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_profiles'
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"
    
    def clean(self):
        if self.preferred_notification in ['sms', 'both'] and not self.phone_number:
            raise ValidationError('Phone number required for SMS notifications.')
    
    def __str__(self):
        return f"{self.user.username} - Customer Profile"

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Features
    max_services = models.PositiveIntegerField(default=10)
    featured_listing = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    features = models.JSONField(default=dict, help_text="Additional features configuration")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subscription_plans'
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class DealerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dealer_profile')
    
    # Business Information
    business_name = models.CharField(max_length=200)
    business_license = models.CharField(max_length=100, unique=True)
    business_type = models.CharField(
        max_length=50,
        choices=[
            ('garage', 'Auto Garage'),
            ('workshop', 'Service Workshop'), 
            ('mobile_service', 'Mobile Service'),
            ('dealership', 'Car Dealership')
        ],
        default='garage'
    )
    
    # Location Details
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    service_radius = models.PositiveIntegerField(default=10, help_text="Service radius in KM")
    
    # Contact Information
    business_phone = models.CharField(max_length=20)
    business_email = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    
    # Financial Information
    bank_account_name = models.CharField(max_length=200)
    bank_account_number = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^\d{8,20}$', 'Invalid bank account number')]
    )
    bank_name = models.CharField(max_length=100)
    bank_routing_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d{9}$', 'Invalid routing number')]
    )
    
    # Commission & Subscription
    commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Platform commission percentage"
    )
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status & Performance
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_bookings = models.PositiveIntegerField(default=0)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Business Hours
    business_hours = models.JSONField(
        default=dict, 
        help_text="Business operating hours in format: {'monday': {'is_open': true, 'start': '09:00', 'end': '18:00'}}"
    )
    
    # External Integration
    has_external_website = models.BooleanField(default=False)
    external_api_url = models.URLField(blank=True, null=True)
    api_key = models.CharField(max_length=100, unique=True, blank=True)
    webhook_url = models.URLField(blank=True, null=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dealer_profiles'
        verbose_name = "Dealer Profile"
        verbose_name_plural = "Dealer Profiles"
        indexes = [
            models.Index(fields=['is_approved', 'is_active']),
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['rating', '-total_reviews']),
        ]
    
    def __str__(self):
        return f"{self.business_name} ({self.user.username})"

class CommissionHistory(models.Model):
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE, related_name='commission_history')
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    effective_date = models.DateTimeField()
    reason = models.TextField(blank=True, help_text="Reason for commission change")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'commission_history'
        verbose_name = "Commission History"
        verbose_name_plural = "Commission Histories"
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['effective_date']),
        ]
    
    def __str__(self):
        return f"{self.dealer.business_name} - {self.commission_percentage}% from {self.effective_date}"

# =============================================================================
# 2. VEHICLE MANAGEMENT
# =============================================================================

class VehicleMake(models.Model):
    name = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(upload_to='vehicle_makes/', blank=True)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vehicle_makes'
        verbose_name = "Vehicle Make"
        verbose_name_plural = "Vehicle Makes"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class VehicleModel(models.Model):
    make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=50)
    year_from = models.PositiveIntegerField()
    year_to = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vehicle_models'
        verbose_name = "Vehicle Model"
        verbose_name_plural = "Vehicle Models"
        unique_together = ['make', 'name']
        ordering = ['make__name', 'name']
    
    def __str__(self):
        return f"{self.make.name} {self.name}"

class Vehicle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    
    # Vehicle Details
    make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE)
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    color = models.CharField(max_length=30, blank=True)
    license_plate = models.CharField(max_length=20, unique=True)
    vin = models.CharField(max_length=17, unique=True, blank=True)
    
    # Technical Specifications
    fuel_type = models.CharField(
        max_length=20,
        choices=[
            ('petrol', 'Petrol'),
            ('diesel', 'Diesel'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('cng', 'CNG')
        ]
    )
    transmission = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual'), ('automatic', 'Automatic')],
        blank=True
    )
    engine_cc = models.PositiveIntegerField(null=True, blank=True)
    current_mileage = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Service History
    last_service_date = models.DateField(null=True, blank=True)
    next_service_due = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['license_plate']),
        ]
    
    def __str__(self):
        return f"{self.make.name} {self.model.name} ({self.license_plate})"

# =============================================================================
# 3. SERVICE MANAGEMENT
# =============================================================================

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Service attributes
    estimated_duration = models.PositiveIntegerField(default=60, help_text="Default duration in minutes")
    requires_vehicle_drop = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_categories'
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name

class Service(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    
    # Service Details
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Service Configuration
    estimated_duration = models.PositiveIntegerField(help_text="Duration in minutes")
    max_concurrent_slots = models.PositiveIntegerField(default=1, help_text="Max simultaneous bookings")
    
    # Vehicle Support
    supported_makes = models.ManyToManyField(VehicleMake, blank=True)
    supported_fuel_types = models.JSONField(default=list)
    min_year = models.PositiveIntegerField(null=True, blank=True)
    max_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Business Rules
    advance_booking_hours = models.PositiveIntegerField(default=2)
    cancellation_hours = models.PositiveIntegerField(default=24)
    
    # Features
    includes = models.JSONField(default=list, help_text="What's included in service")
    requirements = models.JSONField(default=list, help_text="Customer requirements")
    
    # Service Type
    service_location = models.CharField(
        max_length=20,
        choices=[
            ('workshop', 'At Workshop'),
            ('customer_location', 'At Customer Location'),
            ('both', 'Both Available')
        ],
        default='workshop'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # External Integration
    external_service_id = models.CharField(max_length=100, blank=True, null=True)
    sync_with_external = models.BooleanField(default=False)
    
    # Analytics
    total_bookings = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services'
        verbose_name = "Service"
        verbose_name_plural = "Services"
        indexes = [
            models.Index(fields=['dealer', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['external_service_id']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.dealer.username}"

class Technician(models.Model):
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE, related_name='technicians')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)
    expertise = models.JSONField(default=list, help_text="List of service categories technician can handle")
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'technicians'
        verbose_name = "Technician"
        verbose_name_plural = "Technicians"
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.dealer.business_name}"

class ServiceSlot(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='slots')
    
    # Time Information
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Capacity Management
    total_capacity = models.PositiveIntegerField(default=1, help_text="Total slots available")
    available_capacity = models.PositiveIntegerField(default=1, help_text="Currently available slots")
    
    # Pricing (can override service base price)
    custom_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Assignment
    assigned_technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False, help_text="Manually blocked by dealer")
    block_reason = models.CharField(max_length=255, blank=True)
    
    # External Integration
    external_slot_id = models.CharField(max_length=100, blank=True, null=True)
    sync_with_external = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_slots'
        verbose_name = "Service Slot"
        verbose_name_plural = "Service Slots"
        unique_together = ['service', 'date', 'start_time']
        indexes = [
            models.Index(fields=['service', 'date', 'start_time']),
            models.Index(fields=['date', 'is_active']),
            models.Index(fields=['external_slot_id']),
        ]
    
    @property
    def is_available(self):
        return self.is_active and not self.is_blocked and self.available_capacity > 0
    
    def __str__(self):
        return f"{self.service.name} - {self.date} {self.start_time}"

# =============================================================================
# 4. BOOKING SYSTEM WITH CANCELLATION POLICIES
# =============================================================================

class CancellationPolicy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Time-based rules
    free_cancellation_hours = models.PositiveIntegerField(default=24)
    partial_refund_hours = models.PositiveIntegerField(default=12)
    no_refund_hours = models.PositiveIntegerField(default=2)
    
    # Refund percentages
    partial_refund_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    
    # Penalties
    no_show_penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    late_cancellation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cancellation_policies'
        verbose_name = "Cancellation Policy"
        verbose_name_plural = "Cancellation Policies"
    
    def __str__(self):
        return self.name

class Promotion(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Promotion Type
    promotion_type = models.CharField(
        max_length=30,
        choices=[
            ('percentage', 'Percentage Discount'),
            ('fixed_amount', 'Fixed Amount Discount'),
            ('first_booking', 'First Booking Discount'),
            ('loyalty_points', 'Bonus Loyalty Points')
        ],
        default='percentage'
    )
    
    # Discount Values
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    bonus_points = models.PositiveIntegerField(default=0)
    
    # Targeting
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Users'),
            ('new_users', 'New Users'),
            ('returning_users', 'Returning Users'),
            ('vip_users', 'VIP Users')
        ],
        default='all'
    )
    
    # Applicable services
    applicable_services = models.ManyToManyField(Service, blank=True)
    applicable_categories = models.ManyToManyField(ServiceCategory, blank=True)
    minimum_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promotions'
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title}"

class Booking(models.Model):
    # Booking ID for customer reference
    booking_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Participants
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service_slot = models.ForeignKey(ServiceSlot, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Booking Details
    booking_for = models.CharField(
        max_length=20,
        choices=[('self', 'Self'), ('friend', 'Friend'), ('family', 'Family')],
        default='self'
    )
    contact_name = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    friend_vehicle_info = models.JSONField(null=True, blank=True)
    
    # Service Location
    service_location = models.CharField(
        max_length=20,
        choices=[
            ('workshop', 'At Workshop'),
            ('customer_location', 'At Customer Location')
        ],
        default='workshop'
    )
    customer_address = models.TextField(blank=True)
    
    # Source tracking
    source = models.CharField(
        max_length=20,
        choices=[('app', 'Mobile App'), ('external', 'External System')],
        default='app'
    )
    
    # Status Management
    status = models.CharField(
        max_length=30,
        choices=[
            ('pending', 'Pending Confirmation'),
            ('confirmed', 'Confirmed'),
            ('in_progress', 'Service In Progress'),
            ('completed', 'Completed'),
            ('cancelled_by_customer', 'Cancelled by Customer'),
            ('cancelled_by_dealer', 'Cancelled by Dealer'),
            ('no_show', 'Customer No Show'),
            ('expired', 'Expired')
        ],
        default='pending'
    )
    
    # Financial Details
    service_amount = models.DecimalField(max_digits=8, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    dealer_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Policies
    cancellation_policy = models.ForeignKey(CancellationPolicy, on_delete=models.SET_NULL, null=True)
    
    # Timing
    booking_deadline = models.DateTimeField(help_text="Deadline for dealer response")
    service_scheduled_at = models.DateTimeField()
    service_started_at = models.DateTimeField(null=True, blank=True)
    service_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Communication
    special_instructions = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # External Integration
    external_booking_id = models.CharField(max_length=100, blank=True, null=True)
    payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=['booking_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['source']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            import random, string
            self.booking_number = f"CS{timezone.now().strftime('%y%m%d')}{''.join(random.choices(string.digits, k=4))}"
        super().save(*args, **kwargs)
    
    def get_cancellation_fee(self):
        """Calculate cancellation fee based on policy and timing"""
        if not self.cancellation_policy:
            return Decimal('0.00')
        
        hours_until_service = (self.service_scheduled_at - timezone.now()).total_seconds() / 3600
        
        if hours_until_service >= self.cancellation_policy.free_cancellation_hours:
            return Decimal('0.00')
        elif hours_until_service >= self.cancellation_policy.partial_refund_hours:
            return self.total_amount * (Decimal('100.00') - self.cancellation_policy.partial_refund_percentage) / Decimal('100.00')
        else:
            return self.total_amount  # Full charge
    
    def clean(self):
        # Validate status transitions
        valid_transitions = {
            'pending': ['confirmed', 'cancelled_by_customer', 'cancelled_by_dealer', 'expired'],
            'confirmed': ['in_progress', 'cancelled_by_customer', 'cancelled_by_dealer'],
            'in_progress': ['completed', 'no_show'],
        }
        if self.pk:  # Only validate on update
            old_instance = Booking.objects.get(pk=self.pk)
            if old_instance.status in valid_transitions and self.status not in valid_transitions[old_instance.status]:
                raise ValidationError(f"Invalid status transition from {old_instance.status} to {self.status}")
    
    def __str__(self):
        return f"Booking {self.booking_number} - {self.customer.username}"

# =============================================================================
# 5. PAYMENT SYSTEM
# =============================================================================

class VirtualCard(models.Model):
    dealer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='virtual_card')
    card_number = models.CharField(
        max_length=16,
        unique=True,
        validators=[RegexValidator(r'^\d{16}$', 'Invalid card number')]
    )
    last_four_digits = models.CharField(max_length=4)
    expiry_date = models.CharField(max_length=5)  # MM/YY format
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    external_card_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'virtual_cards'
        verbose_name = "Virtual Card"
        verbose_name_plural = "Virtual Cards"
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['card_number']),
        ]
    
    def save(self, *args, **kwargs):
        if self.card_number:
            self.last_four_digits = self.card_number[-4:]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Virtual Card ****{self.last_four_digits} - {self.dealer.username}"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    
    # Payment Details
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True, blank=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('succeeded', 'Succeeded'),
            ('failed', 'Failed'),
            ('canceled', 'Canceled'),
            ('refunded', 'Refunded'),
            ('partially_refunded', 'Partially Refunded')
        ],
        default='pending'
    )
    
    # Payment Method
    payment_method_type = models.CharField(
        max_length=50,
        choices=[
            ('customer_card', 'Customer Card'),
            ('virtual_card', 'Dealer Virtual Card'),
            ('mobile_banking', 'Mobile Banking'),
            ('bank_transfer', 'Bank Transfer'),
            ('external', 'External Payment')
        ],
        default='customer_card'
    )
    payment_method_details = models.JSONField(null=True, blank=True)
    virtual_card = models.ForeignKey(VirtualCard, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Gateway Response
    gateway_response = models.JSONField(null=True, blank=True)
    
    # Timestamps
    authorized_at = models.DateTimeField(null=True, blank=True)
    captured_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Refund tracking
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    failure_code = models.CharField(max_length=50, blank=True)
    failure_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method_type']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - Booking {self.booking.booking_number}"

class PayoutRequest(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    
    # Banking Details
    bank_details = models.JSONField(help_text="Bank account details for payout")
    
    # Processing
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payouts')
    admin_notes = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # External reference
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payout_requests'
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payout Request {self.id} - {self.dealer.username} - {self.amount}"

class BalanceTransaction(models.Model):
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE, related_name='balance_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    transaction_type = models.CharField(
        max_length=25,  # Increased from 20 to 25
        choices=[
            ('booking', 'Booking Completion'),
            ('payout', 'Payout'),
            ('refund', 'Refund'),
            ('adjustment', 'Manual Adjustment'),
            ('commission_adjustment', 'Commission Adjustment')
        ]
    )
    description = models.TextField(blank=True)
    
    # Related objects
    related_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    related_payout = models.ForeignKey(PayoutRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Balance tracking
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'balance_transactions'
        verbose_name = "Balance Transaction"
        verbose_name_plural = "Balance Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.dealer.business_name} - {self.transaction_type} ({self.amount})"

# =============================================================================
# 6. LOYALTY SYSTEM
# =============================================================================

class LoyaltyTransaction(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('earned', 'Points Earned'),
            ('redeemed', 'Points Redeemed'),
            ('expired', 'Points Expired'),
            ('bonus', 'Bonus Points'),
            ('adjustment', 'Manual Adjustment')
        ]
    )
    points = models.IntegerField(help_text="Can be negative for redemptions")
    description = models.CharField(max_length=255)
    
    # Related objects
    related_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    related_promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Balance tracking
    balance_before = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'loyalty_transactions'
        verbose_name = "Loyalty Transaction"
        verbose_name_plural = "Loyalty Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.transaction_type} ({self.points} points)"

# =============================================================================
# 7. REVIEWS & RATINGS
# =============================================================================

class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    
    # Ratings
    overall_rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    service_quality = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    punctuality = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    value_for_money = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    
    # Review Content
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    
    # Photos
    photos = models.JSONField(default=list, blank=True, help_text="List of photo URLs")
    
    # Status
    is_published = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Dealer Response
    dealer_response = models.TextField(blank=True)
    dealer_response_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ['customer', 'booking']
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['is_published']),
        ]
    
    def __str__(self):
        return f"Review by {self.customer.username} for {self.dealer.username}"

# =============================================================================
# 8. EXTERNAL INTEGRATION SYSTEM
# =============================================================================

class ExternalIntegration(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integrations')
    
    name = models.CharField(max_length=100)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255)
    webhook_url = models.URLField(blank=True)
    
    # Configuration
    sync_services = models.BooleanField(default=True)
    sync_slots = models.BooleanField(default=True)
    sync_bookings = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'external_integrations'
        verbose_name = "External Integration"
        verbose_name_plural = "External Integrations"
    
    def __str__(self):
        return f"{self.name} - {self.dealer.username}"

class WebhookEvent(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhook_events')
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('service.created', 'Service Created'),
            ('service.updated', 'Service Updated'),
            ('service.deleted', 'Service Deleted'),
            ('slot.created', 'Slot Created'),
            ('slot.updated', 'Slot Updated'),
            ('slot.deleted', 'Slot Deleted'),
            ('booking.created', 'Booking Created'),
            ('booking.updated', 'Booking Updated'),
            ('booking.cancelled', 'Booking Cancelled'),
        ]
    )
    event_data = models.JSONField()
    external_id = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_events'
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.dealer.username}"

class SyncLog(models.Model):
    integration = models.ForeignKey(ExternalIntegration, on_delete=models.CASCADE, related_name='sync_logs')
    
    sync_type = models.CharField(
        max_length=20,
        choices=[
            ('service_push', 'Service Push'),
            ('service_pull', 'Service Pull'),
            ('slot_push', 'Slot Push'),
            ('slot_pull', 'Slot Pull'),
            ('booking_push', 'Booking Push'),
            ('booking_pull', 'Booking Pull')
        ]
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial Success')
        ]
    )
    
    # Data
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metrics
    records_processed = models.PositiveIntegerField(default=0)
    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sync_logs'
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sync_type} - {self.status}"

# =============================================================================
# 9. NOTIFICATION SYSTEM
# =============================================================================

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100)
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('booking_confirmed', 'Booking Confirmed'),
            ('booking_cancelled', 'Booking Cancelled'),
            ('service_reminder', 'Service Reminder'),
            ('payment_success', 'Payment Success'),
            ('payout_processed', 'Payout Processed'),
            ('review_request', 'Review Request')
        ]
    )
    
    # Templates
    email_subject = models.CharField(max_length=255, blank=True)
    email_body = models.TextField(blank=True)
    sms_message = models.TextField(blank=True)
    push_title = models.CharField(max_length=100, blank=True)
    push_body = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_templates'
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
    
    def __str__(self):
        return f"{self.name} - {self.event_type}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Channel
    channel = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('sms', 'SMS'), ('push', 'Push Notification')]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')],
        default='pending'
    )
    
    # Related objects
    related_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['status']),
            models.Index(fields=['channel']),
        ]
    
    def __str__(self):
        return f"Notification to {self.recipient.username} - {self.title}"

# =============================================================================
# 10. VERIFICATION SYSTEM
# =============================================================================

class DealerVerificationDocument(models.Model):
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE, related_name='verification_documents')
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('trade_license', 'Trade License'),
            ('business_registration', 'Business Registration Certificate'),
            ('national_id', 'National ID (NID)'),
            ('tin_certificate', 'TIN Certificate'),
            ('address_proof', 'Proof of Business Address'),
        ]
    )
    document_file = models.FileField(upload_to='dealer_verification_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_documents')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'dealer_verification_documents'
        verbose_name = "Dealer Verification Document"
        verbose_name_plural = "Dealer Verification Documents"
        unique_together = ['dealer', 'document_type']
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['document_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.dealer.business_name} - {self.get_document_type_display()}"

class CustomerVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone OTP'),
            ('email', 'Email Verification'),
            ('national_id', 'National ID'),
        ]
    )
    token = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_verifications'
        verbose_name = "Customer Verification"
        verbose_name_plural = "Customer Verifications"
        unique_together = ['user', 'verification_type']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_verification_type_display()}"

# =============================================================================
# 11. ANALYTICS & REPORTING
# =============================================================================

class BookingAnalytics(models.Model):
    date = models.DateField(unique=True)
    
    # Booking metrics
    total_bookings = models.PositiveIntegerField(default=0)
    confirmed_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    cancelled_bookings = models.PositiveIntegerField(default=0)
    no_show_bookings = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    dealer_payouts = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Customer metrics
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_analytics'
        verbose_name = "Booking Analytics"
        verbose_name_plural = "Booking Analytics"
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"

class DealerAnalytics(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Performance metrics
    total_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    cancelled_bookings = models.PositiveIntegerField(default=0)
    no_show_bookings = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    platform_fees_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Service metrics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    new_reviews = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dealer_analytics'
        verbose_name = "Dealer Analytics"
        verbose_name_plural = "Dealer Analytics"
        unique_together = ['dealer', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.dealer.username} - {self.date}"

# =============================================================================
# 12. SYSTEM CONFIGURATION & ADMIN TRACKING
# =============================================================================

class SystemConfiguration(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON')
        ],
        default='string'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_configurations'
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"
    
    def __str__(self):
        return f"{self.key}: {self.value}"

class AdminAction(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('dealer_approved', 'Dealer Approved'),
            ('dealer_suspended', 'Dealer Suspended'),
            ('service_featured', 'Service Featured'),
            ('payout_processed', 'Payout Processed'),
            ('promotion_created', 'Promotion Created'),
            ('document_verified', 'Document Verified')
        ]
    )
    target_model = models.CharField(max_length=50)
    target_id = models.PositiveIntegerField()
    description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_actions'
        verbose_name = "Admin Action"
        verbose_name_plural = "Admin Actions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action_type} by {self.admin_user.username}"

# =============================================================================
# 13. ADDITIONAL BOOKING FEATURES
# =============================================================================

class ServiceAddon(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_addons'
        verbose_name = "Service Addon"
        verbose_name_plural = "Service Addons"
    
    def __str__(self):
        return f"{self.service.name} - {self.name}"

class BookingAddon(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='addons')
    addon = models.ForeignKey(ServiceAddon, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        db_table = 'booking_addons'
        verbose_name = "Booking Addon"
        verbose_name_plural = "Booking Addons"
        unique_together = ['booking', 'addon']
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.booking.booking_number} - {self.addon.name}"

class BookingStatusHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_status_history'
        verbose_name = "Booking Status History"
        verbose_name_plural = "Booking Status Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.booking.booking_number} - {self.old_status} -> {self.new_status}"

# =============================================================================
# 14. SUPPORT & HELP SYSTEM
# =============================================================================

class SupportTicket(models.Model):
    ticket_number = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    
    # Ticket Details
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('booking_issue', 'Booking Issue'),
            ('payment_problem', 'Payment Problem'),
            ('account_issue', 'Account Issue'),
            ('service_issue', 'Service Issue'),
            ('other', 'Other')
        ],
        default='other'
    )
    
    # Status Management
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed')
        ],
        default='open'
    )
    
    # Priority
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        default='medium'
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets'
    )
    
    # Related Objects
    related_booking = models.ForeignKey(
        'Booking', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='support_tickets'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'support_tickets'
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['user']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import random, string
            self.ticket_number = f"T{timezone.now().strftime('%y%m%d')}{''.join(random.choices(string.digits, k=4))}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.subject}"

class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='support_messages'
    )
    
    # Message Content
    message = models.TextField()
    attachment = models.FileField(
        upload_to='support_attachments/', 
        blank=True, 
        null=True
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'support_messages'
        verbose_name = "Support Message"
        verbose_name_plural = "Support Messages"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket']),
            models.Index(fields=['sender']),
        ]
    
    def __str__(self):
        return f"Message for Ticket {self.ticket.ticket_number} by {self.sender.username}"

# =============================================================================
# 15. PAYOUT SYSTEM (INCLUDING DealerPayout)
# =============================================================================

class DealerPayout(models.Model):
    dealer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payouts'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    processing_fee = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00
    )
    net_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    
    # Banking Details
    bank_details = models.JSONField(
        help_text="Bank account details for payout (e.g., {'account_number': 'xxx', 'bank_name': 'xxx'})"
    )
    
    # Processing Information
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_dealer_payouts'
    )
    admin_notes = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Transaction Reference
    transaction_reference = models.CharField(
        max_length=100, 
        blank=True, 
        unique=True
    )
    
    # Related Bookings
    related_bookings = models.ManyToManyField(
        'Booking', 
        blank=True, 
        related_name='payouts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dealer_payouts'
        verbose_name = "Dealer Payout"
        verbose_name_plural = "Dealer Payouts"
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.transaction_reference:
            self.transaction_reference = f"PAY{timezone.now().strftime('%y%m%d')}{secrets.token_hex(4).upper()}"
        self.net_amount = self.amount - self.processing_fee
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payout {self.transaction_reference} - {self.dealer.username} - {self.amount}"

# =============================================================================
# SIGNALS
# =============================================================================

@receiver(post_save, sender=SupportTicket)
def notify_admin_on_ticket_creation(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.assigned_to or User.objects.filter(is_staff=True).first(),
            title="New Support Ticket Created",
            message=f"New support ticket {instance.ticket_number} created by {instance.user.username}: {instance.subject}",
            channel='email'
        )

@receiver(post_save, sender=SupportMessage)
def notify_ticket_participants(sender, instance, created, **kwargs):
    if created:
        recipient = instance.ticket.assigned_to if instance.sender == instance.ticket.user else instance.ticket.user
        Notification.objects.create(
            recipient=recipient,
            title=f"New Message in Ticket {instance.ticket.ticket_number}",
            message=f"New message from {instance.sender.username}: {instance.message[:100]}...",
            channel='email'
        )

@receiver(post_save, sender=DealerPayout)
def update_dealer_balance_on_payout(sender, instance, created, **kwargs):
    if created and instance.status == 'completed':
        dealer_profile = instance.dealer.dealer_profile
        dealer_profile.current_balance -= instance.net_amount
        dealer_profile.save(update_fields=['current_balance'])
        
        BalanceTransaction.objects.create(
            dealer=dealer_profile,
            amount=-instance.net_amount,
            transaction_type='payout',
            description=f"Payout {instance.transaction_reference}",
            related_payout=instance,
            balance_before=dealer_profile.current_balance + instance.net_amount,
            balance_after=dealer_profile.current_balance
        )

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_support_ticket(user, subject, description, category='other', priority='medium'):
    """Utility function to create a support ticket"""
    ticket = SupportTicket.objects.create(
        user=user,
        subject=subject,
        description=description,
        category=category,
        priority=priority
    )
    return ticket

def process_dealer_payout(dealer, amount, bank_details):
    """Utility function to process a dealer payout"""
    payout = DealerPayout.objects.create(
        dealer=dealer,
        amount=amount,
        bank_details=bank_details,
        processing_fee=amount * Decimal('0.02'),  # Example: 2% processing fee
    )
    return payout
