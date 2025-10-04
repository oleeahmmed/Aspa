
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from ..models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
# =============================================================================
# USER & AUTHENTICATION
# =============================================================================


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')
        password = attrs.get('password')

        # Check if either email or username is provided
        if not email and not username:
            raise serializers.ValidationError(
                {'error': 'Must provide either email or username'}
            )

        if not password:
            raise serializers.ValidationError(
                {'error': 'Password is required'}
            )

        # Try to find user by email or username
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'error': 'Invalid credentials'}
                )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError(
                {'error': 'Invalid credentials'}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'error': 'User account is disabled'}
            )

        attrs['user'] = user
        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer to allow login with either username or email"""
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        # Get username or email from input
        username_or_email = attrs.get('username') or attrs.get('email')
        password = attrs.get('password')

        if username_or_email and password:
            # Try to find user by email first
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                # If email not found, assume it's a username
                username = username_or_email

            # Authenticate user
            user = authenticate(request=self.context.get('request'), username=username, password=password)

            if not user:
                raise serializers.ValidationError(
                    {'error': 'No active account found with the given credentials'},
                    code='authentication'
                )

            # Generate tokens
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)
            data['user'] = UserSerializer(user, context=self.context).data

            return data
        raise serializers.ValidationError(
            {'error': 'Must include username or email and password'},
            code='authentication'
        )

class UserSerializer(serializers.ModelSerializer):
    profile_type = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'date_joined', 'profile_type']
        read_only_fields = ['id', 'date_joined']
    
    def get_profile_type(self, obj):
        if hasattr(obj, 'customer_profile'):
            return 'customer'
        elif hasattr(obj, 'dealer_profile'):
            return 'dealer'
        return 'admin' if obj.is_staff else 'unknown'

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

# =============================================================================
# PROFILES
# =============================================================================

class CustomerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields = ['user', 'total_bookings', 'total_spent', 'loyalty_points', 
                            'created_at', 'updated_at']

    def validate(self, data):
        # Custom validation for preferred_notification
        if data.get('preferred_notification') in ['sms', 'both'] and not data.get('phone_number'):
            raise serializers.ValidationError('Phone number required for SMS notifications.')
        return data

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['created_at']


class DealerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    subscription_plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    
    class Meta:
        model = DealerProfile
        fields = '__all__'
        read_only_fields = ['user', 'rating', 'total_reviews', 'total_bookings', 
                            'current_balance', 'api_key', 'created_at', 'updated_at']

    def validate(self, data):
        # Custom validation for latitude/longitude (optional, but ensure format)
        if 'latitude' in data and not (-90 <= data['latitude'] <= 90):
            raise serializers.ValidationError('Latitude must be between -90 and 90.')
        if 'longitude' in data and not (-180 <= data['longitude'] <= 180):
            raise serializers.ValidationError('Longitude must be between -180 and 180.')
        return data

class CommissionHistorySerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.business_name', read_only=True)
    
    class Meta:
        model = CommissionHistory
        fields = '__all__'
        read_only_fields = ['created_at']

class CustomerVerificationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CustomerVerification
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class DealerVerificationDocumentSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.business_name', read_only=True)
    
    class Meta:
        model = DealerVerificationDocument
        fields = '__all__'
        read_only_fields = ['dealer', 'uploaded_at', 'reviewed_by', 'reviewed_at']

# =============================================================================
# VEHICLES
# =============================================================================

class VehicleMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMake
        fields = '__all__'
        read_only_fields = ['created_at']

class VehicleModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)
    
    class Meta:
        model = VehicleModel
        fields = '__all__'
        read_only_fields = ['created_at']

class VehicleSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

# =============================================================================
# SERVICES
# =============================================================================

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'
        read_only_fields = ['created_at']

class ServiceSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['dealer', 'total_bookings', 'view_count', 
                           'created_at', 'updated_at']

class ServiceAddonSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = ServiceAddon
        fields = '__all__'
        read_only_fields = ['created_at']

class TechnicianSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.business_name', read_only=True)
    
    class Meta:
        model = Technician
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ServiceSlotSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    technician_name = serializers.CharField(source='assigned_technician.name', read_only=True)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = ServiceSlot
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

# =============================================================================
# BOOKINGS
# =============================================================================

class CancellationPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = CancellationPolicy
        fields = '__all__'
        read_only_fields = ['created_at']

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ['current_uses', 'created_at']

class BookingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    service_name = serializers.CharField(source='service_slot.service.name', read_only=True)
    vehicle_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_number', 'customer', 'created_at', 'updated_at']
    
    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.make.name} {obj.vehicle.model.name} ({obj.vehicle.license_plate})"

class BookingAddonSerializer(serializers.ModelSerializer):
    addon_name = serializers.CharField(source='addon.name', read_only=True)
    
    class Meta:
        model = BookingAddon
        fields = '__all__'

class BookingStatusHistorySerializer(serializers.ModelSerializer):
    booking_number = serializers.CharField(source='booking.booking_number', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = BookingStatusHistory
        fields = '__all__'
        read_only_fields = ['created_at']

# =============================================================================
# PAYMENTS
# =============================================================================

class VirtualCardSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    
    class Meta:
        model = VirtualCard
        fields = '__all__'
        read_only_fields = ['dealer', 'last_four_digits', 'created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    booking_number = serializers.CharField(source='booking.booking_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class DealerPayoutSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)
    
    class Meta:
        model = DealerPayout
        fields = '__all__'
        read_only_fields = ['dealer', 'net_amount', 'transaction_reference', 
                           'processed_by', 'processed_at', 'created_at', 'updated_at']

class PayoutRequestSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    
    class Meta:
        model = PayoutRequest
        fields = '__all__'
        read_only_fields = ['dealer', 'net_amount', 'processed_by', 
                           'processed_at', 'created_at']

class BalanceTransactionSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.business_name', read_only=True)
    
    class Meta:
        model = BalanceTransaction
        fields = '__all__'
        read_only_fields = ['created_at']

# =============================================================================
# LOYALTY & REVIEWS
# =============================================================================

class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'
        read_only_fields = ['customer', 'balance_before', 'balance_after', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    booking_number = serializers.CharField(source='booking.booking_number', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['customer', 'dealer', 'created_at']

# =============================================================================
# NOTIFICATIONS
# =============================================================================

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at']

class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at']

# =============================================================================
# SUPPORT
# =============================================================================

class SupportTicketSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['ticket_number', 'user', 'created_at', 'updated_at']

class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)
    
    class Meta:
        model = SupportMessage
        fields = '__all__'
        read_only_fields = ['sender', 'created_at']

# =============================================================================
# INTEGRATIONS
# =============================================================================

class ExternalIntegrationSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    
    class Meta:
        model = ExternalIntegration
        fields = '__all__'
        read_only_fields = ['dealer', 'last_sync_at', 'last_sync_status', 
                           'created_at', 'updated_at']

class WebhookEventSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    
    class Meta:
        model = WebhookEvent
        fields = '__all__'
        read_only_fields = ['created_at', 'processed_at']

class SyncLogSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    
    class Meta:
        model = SyncLog
        fields = '__all__'
        read_only_fields = ['created_at']

# =============================================================================
# ANALYTICS
# =============================================================================

class BookingAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAnalytics
        fields = '__all__'
        read_only_fields = ['created_at']

class DealerAnalyticsSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField(source='dealer.username', read_only=True)
    
    class Meta:
        model = DealerAnalytics
        fields = '__all__'
        read_only_fields = ['created_at']

# =============================================================================
# SYSTEM
# =============================================================================

class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AdminActionSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin_user.username', read_only=True)
    
    class Meta:
        model = AdminAction
        fields = '__all__'
        read_only_fields = ['admin_user', 'created_at']