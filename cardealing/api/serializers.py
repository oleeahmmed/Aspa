from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.utils import timezone
from decimal import Decimal
from ..models import *


# =============================================================================
# AUTHENTICATION SERIALIZERS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile information"""
    profile_type = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'date_joined', 'profile_type']
        read_only_fields = ['id', 'date_joined']
    
    def get_profile_type(self, obj):
        if hasattr(obj, 'customer_profile'):
            return 'customer'
        elif hasattr(obj, 'dealer_profile'):
            return 'dealer'
        return 'admin' if obj.is_staff else 'unknown'


class GroupSerializer(serializers.ModelSerializer):
    """Group serializer for permissions management"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(
        choices=['customer', 'dealer'], 
        write_only=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'password', 'password_confirm', 'user_type']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(**validated_data)
        
        # Create appropriate profile
        if user_type == 'customer':
            CustomerProfile.objects.create(user=user)
        elif user_type == 'dealer':
            DealerProfile.objects.create(
                user=user,
                business_name=f"{user.first_name} {user.last_name} Business",
                address="To be updated",
                city="To be updated",
                postal_code="00000",
                latitude=0.0,
                longitude=0.0,
                business_phone="To be updated",
                bank_account_name=f"{user.first_name} {user.last_name}",
                bank_account_number="0000000000",
                bank_name="To be updated",
                bank_routing_number="000000000"
            )
        
        return user


# =============================================================================
# USER PROFILE SERIALIZERS
# =============================================================================

class CustomerProfileSerializer(serializers.ModelSerializer):
    """Customer profile serializer"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields = ['total_bookings', 'total_spent', 'loyalty_points', 
                           'created_at', 'updated_at']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Subscription plan serializer"""
    
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['created_at']


class DealerProfileSerializer(serializers.ModelSerializer):
    """Dealer profile serializer"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    subscription_plan_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = DealerProfile
        fields = '__all__'
        read_only_fields = ['rating', 'total_reviews', 'total_bookings', 
                           'current_balance', 'api_key', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Generate API key for new dealers
        import secrets
        validated_data['api_key'] = secrets.token_urlsafe(32)
        return super().create(validated_data)


class CommissionHistorySerializer(serializers.ModelSerializer):
    """Commission history serializer"""
    dealer = DealerProfileSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CommissionHistory
        fields = '__all__'
        read_only_fields = ['created_at']


# =============================================================================
# VEHICLE MANAGEMENT SERIALIZERS
# =============================================================================

class VehicleMakeSerializer(serializers.ModelSerializer):
    """Vehicle make serializer"""
    
    class Meta:
        model = VehicleMake
        fields = '__all__'
        read_only_fields = ['created_at']


class VehicleModelSerializer(serializers.ModelSerializer):
    """Vehicle model serializer"""
    make = VehicleMakeSerializer(read_only=True)
    make_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = VehicleModel
        fields = '__all__'
        read_only_fields = ['created_at']


class VehicleSerializer(serializers.ModelSerializer):
    """Vehicle serializer"""
    owner = UserSerializer(read_only=True)
    make = VehicleMakeSerializer(read_only=True)
    model = VehicleModelSerializer(read_only=True)
    make_id = serializers.IntegerField(write_only=True)
    model_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


# =============================================================================
# SERVICE MANAGEMENT SERIALIZERS
# =============================================================================

class ServiceCategorySerializer(serializers.ModelSerializer):
    """Service category serializer"""
    parent = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = ServiceCategory
        fields = '__all__'
        read_only_fields = ['created_at']


class ServiceAddonSerializer(serializers.ModelSerializer):
    """Service addon serializer"""
    
    class Meta:
        model = ServiceAddon
        fields = '__all__'
        read_only_fields = ['created_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Service serializer"""
    dealer = UserSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    supported_makes = VehicleMakeSerializer(many=True, read_only=True)
    supported_make_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )
    addons = ServiceAddonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['dealer', 'total_bookings', 'view_count', 
                           'created_at', 'updated_at']
    
    def create(self, validated_data):
        supported_make_ids = validated_data.pop('supported_make_ids', [])
        validated_data['dealer'] = self.context['request'].user
        
        service = super().create(validated_data)
        
        if supported_make_ids:
            service.supported_makes.set(supported_make_ids)
        
        return service


class TechnicianSerializer(serializers.ModelSerializer):
    """Technician serializer"""
    dealer = DealerProfileSerializer(read_only=True)
    
    class Meta:
        model = Technician
        fields = '__all__'
        read_only_fields = ['dealer', 'created_at', 'updated_at']


class ServiceSlotSerializer(serializers.ModelSerializer):
    """Service slot serializer"""
    service = ServiceSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True)
    assigned_technician = TechnicianSerializer(read_only=True)
    assigned_technician_id = serializers.IntegerField(write_only=True, required=False)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = ServiceSlot
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ServiceAvailabilitySerializer(serializers.ModelSerializer):
    """Service availability serializer for bulk slot creation"""
    service_id = serializers.IntegerField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    time_slots = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    class Meta:
        model = ServiceSlot
        fields = ['service_id', 'date_from', 'date_to', 'time_slots']
    
    def create(self, validated_data):
        # This would be handled in the view to create multiple slots
        pass


# =============================================================================
# BOOKING SYSTEM SERIALIZERS
# =============================================================================

class CancellationPolicySerializer(serializers.ModelSerializer):
    """Cancellation policy serializer"""
    
    class Meta:
        model = CancellationPolicy
        fields = '__all__'
        read_only_fields = ['created_at']


class PromotionSerializer(serializers.ModelSerializer):
    """Promotion serializer"""
    applicable_services = ServiceSerializer(many=True, read_only=True)
    applicable_categories = ServiceCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ['current_uses', 'created_at']


class BookingAddonSerializer(serializers.ModelSerializer):
    """Booking addon serializer"""
    addon = ServiceAddonSerializer(read_only=True)
    addon_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = BookingAddon
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    """Booking serializer"""
    customer = UserSerializer(read_only=True)
    service_slot = ServiceSlotSerializer(read_only=True)
    service_slot_id = serializers.IntegerField(write_only=True)
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.IntegerField(write_only=True)
    promotion = PromotionSerializer(read_only=True)
    promotion_id = serializers.IntegerField(write_only=True, required=False)
    cancellation_policy = CancellationPolicySerializer(read_only=True)
    addons = BookingAddonSerializer(many=True, read_only=True)
    cancellation_fee = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_number', 'customer', 'created_at', 'updated_at']
    
    def get_cancellation_fee(self, obj):
        return obj.get_cancellation_fee()
    
    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    """Booking status history serializer"""
    booking = BookingSerializer(read_only=True)
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = BookingStatusHistory
        fields = '__all__'
        read_only_fields = ['created_at']


# =============================================================================
# PAYMENT SYSTEM SERIALIZERS
# =============================================================================

class VirtualCardSerializer(serializers.ModelSerializer):
    """Virtual card serializer"""
    dealer = UserSerializer(read_only=True)
    
    class Meta:
        model = VirtualCard
        fields = '__all__'
        read_only_fields = ['dealer', 'card_number', 'last_four_digits', 
                           'balance', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""
    booking = BookingSerializer(read_only=True)
    virtual_card = VirtualCardSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DealerPayoutSerializer(serializers.ModelSerializer):
    """Dealer payout serializer"""
    dealer = UserSerializer(read_only=True)
    processed_by = UserSerializer(read_only=True)
    related_bookings = BookingSerializer(many=True, read_only=True)
    
    class Meta:
        model = DealerPayout
        fields = '__all__'
        read_only_fields = ['dealer', 'net_amount', 'transaction_reference', 
                           'processed_by', 'processed_at', 'created_at', 'updated_at']


class PayoutRequestSerializer(serializers.ModelSerializer):
    """Payout request serializer"""
    dealer = UserSerializer(read_only=True)
    processed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = PayoutRequest
        fields = '__all__'
        read_only_fields = ['dealer', 'net_amount', 'processed_by', 
                           'processed_at', 'created_at']


class BalanceTransactionSerializer(serializers.ModelSerializer):
    """Balance transaction serializer"""
    dealer = DealerProfileSerializer(read_only=True)
    related_booking = BookingSerializer(read_only=True)
    related_payout = PayoutRequestSerializer(read_only=True)
    
    class Meta:
        model = BalanceTransaction
        fields = '__all__'
        read_only_fields = ['created_at']


# =============================================================================
# COMMUNICATION SERIALIZERS
# =============================================================================

class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Notification template serializer"""
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    recipient = UserSerializer(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    related_booking = BookingSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Review serializer"""
    customer = UserSerializer(read_only=True)
    dealer = UserSerializer(read_only=True)
    booking = BookingSerializer(read_only=True)
    booking_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['customer', 'dealer', 'created_at']
    
    def create(self, validated_data):
        booking = Booking.objects.get(id=validated_data['booking_id'])
        validated_data['customer'] = self.context['request'].user
        validated_data['dealer'] = booking.service_slot.service.dealer
        validated_data['booking'] = booking
        return super().create(validated_data)


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    """Loyalty transaction serializer"""
    customer = UserSerializer(read_only=True)
    related_booking = BookingSerializer(read_only=True)
    related_promotion = PromotionSerializer(read_only=True)
    
    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'
        read_only_fields = ['customer', 'balance_before', 'balance_after', 'created_at']


# =============================================================================
# SUPPORT SYSTEM SERIALIZERS
# =============================================================================

class SupportTicketSerializer(serializers.ModelSerializer):
    """Support ticket serializer"""
    user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    related_booking = BookingSerializer(read_only=True)
    related_booking_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['ticket_number', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SupportMessageSerializer(serializers.ModelSerializer):
    """Support message serializer"""
    ticket = SupportTicketSerializer(read_only=True)
    ticket_id = serializers.IntegerField(write_only=True)
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = SupportMessage
        fields = '__all__'
        read_only_fields = ['sender', 'created_at']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


# =============================================================================
# VERIFICATION SERIALIZERS
# =============================================================================

class CustomerVerificationSerializer(serializers.ModelSerializer):
    """Customer verification serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CustomerVerification
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class DealerVerificationDocumentSerializer(serializers.ModelSerializer):
    """Dealer verification document serializer"""
    dealer = DealerProfileSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DealerVerificationDocument
        fields = '__all__'
        read_only_fields = ['dealer', 'uploaded_at', 'reviewed_by', 'reviewed_at']


# =============================================================================
# INTEGRATION SERIALIZERS
# =============================================================================

class ExternalIntegrationSerializer(serializers.ModelSerializer):
    """External integration serializer"""
    dealer = UserSerializer(read_only=True)
    
    class Meta:
        model = ExternalIntegration
        fields = '__all__'
        read_only_fields = ['dealer', 'last_sync_at', 'last_sync_status', 
                           'created_at', 'updated_at']


class WebhookConfigurationSerializer(serializers.ModelSerializer):
    """Webhook configuration serializer - placeholder for future implementation"""
    pass


class WebhookEventSerializer(serializers.ModelSerializer):
    """Webhook event serializer"""
    dealer = UserSerializer(read_only=True)
    
    class Meta:
        model = WebhookEvent
        fields = '__all__'
        read_only_fields = ['dealer', 'created_at', 'processed_at']


class SyncLogSerializer(serializers.ModelSerializer):
    """Sync log serializer"""
    integration = ExternalIntegrationSerializer(read_only=True)
    
    class Meta:
        model = SyncLog
        fields = '__all__'
        read_only_fields = ['created_at']


# =============================================================================
# ANALYTICS SERIALIZERS
# =============================================================================

class BookingAnalyticsSerializer(serializers.ModelSerializer):
    """Booking analytics serializer"""
    
    class Meta:
        model = BookingAnalytics
        fields = '__all__'
        read_only_fields = ['created_at']


class DealerAnalyticsSerializer(serializers.ModelSerializer):
    """Dealer analytics serializer"""
    dealer = UserSerializer(read_only=True)
    
    class Meta:
        model = DealerAnalytics
        fields = '__all__'
        read_only_fields = ['dealer', 'created_at']


# =============================================================================
# SYSTEM SERIALIZERS
# =============================================================================

class SystemConfigurationSerializer(serializers.ModelSerializer):
    """System configuration serializer"""
    
    class Meta:
        model = SystemConfiguration
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AdminActionSerializer(serializers.ModelSerializer):
    """Admin action serializer"""
    admin_user = UserSerializer(read_only=True)
    
    class Meta:
        model = AdminAction
        fields = '__all__'
        read_only_fields = ['admin_user', 'created_at']
    
    def create(self, validated_data):
        validated_data['admin_user'] = self.context['request'].user
        return super().create(validated_data)



# =============================================================================
# MOBILE AUTHENTICATION SERIALIZERS (ADD THESE TO YOUR EXISTING FILE)
# =============================================================================

from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer

class CustomUserDetailsSerializer(UserDetailsSerializer):
    """Enhanced user details with profile info for mobile"""
    profile_type = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'profile_type', 'profile_id')
    
    def get_profile_type(self, obj):
        if hasattr(obj, 'customer_profile'):
            return 'customer'
        elif hasattr(obj, 'dealer_profile'):
            return 'dealer'
        return 'unknown'
    
    def get_profile_id(self, obj):
        if hasattr(obj, 'customer_profile'):
            return obj.customer_profile.id
        elif hasattr(obj, 'dealer_profile'):
            return obj.dealer_profile.id
        return None

class CustomRegisterSerializer(RegisterSerializer):
    """Registration with profile type for mobile"""
    user_type = serializers.ChoiceField(
        choices=['customer', 'dealer'], 
        default='customer',
        write_only=True
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['user_type'] = self.validated_data.get('user_type', 'customer')
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        return data
    
    def save(self, request):
        user = super().save(request)
        user_type = self.cleaned_data.get('user_type', 'customer')
        
        # Create profile based on user_type
        if user_type == 'customer':
            CustomerProfile.objects.get_or_create(user=user)
        elif user_type == 'dealer':
            DealerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': f"{user.first_name} {user.last_name} Business",
                    'address': "To be updated",
                    'city': "To be updated",
                    'postal_code': "00000",
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'business_phone': "To be updated",
                    'bank_account_name': f"{user.first_name} {user.last_name}",
                    'bank_account_number': "0000000000",
                    'bank_name': "To be updated",
                    'bank_routing_number': "000000000"
                }
            )
        
        return user