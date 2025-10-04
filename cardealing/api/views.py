# views.py - Enhanced with comprehensive error handling and validation
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

import logging

# Setup logger
logger = logging.getLogger(__name__)

# ====== Serializers ======
from .serializers import (
    CustomTokenObtainPairSerializer, LoginSerializer, UserSerializer, GroupSerializer,
    CustomerProfileSerializer, DealerProfileSerializer,
    SubscriptionPlanSerializer, CommissionHistorySerializer,
    CustomerVerificationSerializer, DealerVerificationDocumentSerializer,
    VehicleMakeSerializer, VehicleModelSerializer, VehicleSerializer,
    ServiceCategorySerializer, ServiceSerializer, ServiceAddonSerializer,
    TechnicianSerializer, ServiceSlotSerializer,
    CancellationPolicySerializer, PromotionSerializer,
    BookingSerializer, BookingAddonSerializer, BookingStatusHistorySerializer,
    VirtualCardSerializer, PaymentSerializer, DealerPayoutSerializer, BalanceTransactionSerializer,
    LoyaltyTransactionSerializer, ReviewSerializer,
    NotificationSerializer, NotificationTemplateSerializer,
    SupportTicketSerializer, SupportMessageSerializer,
    ExternalIntegrationSerializer, WebhookEventSerializer, SyncLogSerializer,
    BookingAnalyticsSerializer, DealerAnalyticsSerializer,
    SystemConfigurationSerializer, AdminActionSerializer,
)

# ====== Models ======
from ..models import (
    CustomerProfile, DealerProfile, SubscriptionPlan, CommissionHistory,
    CustomerVerification, DealerVerificationDocument,
    VehicleMake, VehicleModel, Vehicle,
    ServiceCategory, Service, ServiceAddon, Technician, ServiceSlot,
    CancellationPolicy, Promotion, Booking, BookingAddon, BookingStatusHistory,
    VirtualCard, Payment, DealerPayout, BalanceTransaction,
    LoyaltyTransaction, Review,
    Notification, NotificationTemplate, SupportTicket, SupportMessage,
    ExternalIntegration, WebhookEvent, SyncLog,
    BookingAnalytics, DealerAnalytics, SystemConfiguration, AdminAction,
)

# =============================================================================
# Base Utilities
# =============================================================================

class DefaultPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class BaseAPIView(APIView):
    """Enhanced base view with comprehensive error handling"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = DefaultPagination

    def handle_exception(self, exc):
        """Centralized exception handling"""
        if isinstance(exc, NotFound):
            return self.fail(
                errors={'detail': str(exc)},
                message='রিসোর্স পাওয়া যায়নি',
                status_code=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, PermissionDenied):
            return self.fail(
                errors={'detail': str(exc)},
                message='অনুমতি নেই',
                status_code=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exc, ValidationError):
            return self.fail(
                errors=exc.detail if hasattr(exc, 'detail') else str(exc),
                message='ভ্যালিডেশন ত্রুটি',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, IntegrityError):
            logger.error(f"Database integrity error: {exc}")
            return self.fail(
                errors={'database': 'ডেটাবেস ত্রুটি - ডুপ্লিকেট এন্ট্রি বা সীমাবদ্ধতা লঙ্ঘন'},
                message='ডেটা সংরক্ষণ ব্যর্থ',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        else:
            logger.exception(f"Unexpected error: {exc}")
            return super().handle_exception(exc)

    def ok(self, data=None, message="সফল", status_code=status.HTTP_200_OK, **extra):
        payload = {"success": True, "message": message, "data": data}
        if extra:
            payload.update(extra)
        return Response(payload, status=status_code)

    def fail(self, errors=None, message="ত্রুটি", status_code=status.HTTP_400_BAD_REQUEST, **extra):
        payload = {"success": False, "message": message, "errors": errors or {}}
        if extra:
            payload.update(extra)
        return Response(payload, status=status_code)

    def q(self, request, key, default=None):
        """Get query parameter safely"""
        return request.query_params.get(key, default)

    def paginate(self, request, queryset, serializer_cls):
        """Paginate queryset with error handling"""
        try:
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)
            if page is not None:
                ser = serializer_cls(page, many=True)
                return paginator.get_paginated_response(ser.data)
            ser = serializer_cls(queryset, many=True)
            return Response(ser.data)
        except Exception as e:
            logger.error(f"Pagination error: {e}")
            raise ValidationError("পেজিনেশন প্রক্রিয়াকরণে ত্রুটি")


def ensure_dealer(user):
    """Verify user is a dealer"""
    if not hasattr(user, 'dealer_profile'):
        raise PermissionDenied("শুধুমাত্র ডিলারদের জন্য")


def ensure_admin(user):
    """Verify user is admin"""
    if not user.is_staff:
        raise PermissionDenied("শুধুমাত্র অ্যাডমিনদের জন্য")


def validate_required_fields(data, fields):
    """Validate required fields exist"""
    missing = [f for f in fields if not data.get(f)]
    if missing:
        raise ValidationError({
            'missing_fields': missing,
            'message': f"প্রয়োজনীয় ফিল্ড অনুপস্থিত: {', '.join(missing)}"
        })


# =============================================================================
# AUTH
# =============================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """Enhanced JWT login with better error messages"""
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Login error: {e}")
            return Response({
                'success': False,
                'message': 'লগইন ব্যর্থ',
                'errors': {'detail': 'ভুল ইউজারনেম/ইমেইল অথবা পাসওয়ার্ড'}
            }, status=status.HTTP_401_UNAUTHORIZED)


class LoginView(BaseAPIView):
    """Alternative login endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            ser = LoginSerializer(data=request.data)
            if not ser.is_valid():
                return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি", status.HTTP_400_BAD_REQUEST)

            user = ser.validated_data['user']
            refresh = RefreshToken.for_user(user)

            return self.ok(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserSerializer(user).data
                },
                message="লগইন সফল"
            )
        except Exception as e:
            logger.error(f"Login error: {e}")
            return self.fail(
                errors={'detail': str(e)},
                message="লগইন ব্যর্থ",
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class UserRegistrationView(BaseAPIView):
    """Enhanced user registration with validation"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Validate required fields
            required = ['username', 'email', 'password']
            validate_required_fields(request.data, required)

            username = request.data['username']
            email = request.data['email']
            password = request.data['password']

            # Check existing user
            if User.objects.filter(username=username).exists():
                return self.fail(
                    {'username': 'এই ইউজারনেম ইতিমধ্যে নিবন্ধিত'},
                    "নিবন্ধন ব্যর্থ"
                )

            if User.objects.filter(email=email).exists():
                return self.fail(
                    {'email': 'এই ইমেইল ইতিমধ্যে নিবন্ধিত'},
                    "নিবন্ধন ব্যর্থ"
                )

            # Password validation
            if len(password) < 6:
                return self.fail(
                    {'password': 'পাসওয়ার্ড কমপক্ষে ৬ অক্ষরের হতে হবে'},
                    "পাসওয়ার্ড দুর্বল"
                )

            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=request.data.get('first_name', ''),
                    last_name=request.data.get('last_name', '')
                )

                # Create appropriate profile
                user_type = request.data.get('user_type', 'customer')

                if user_type == 'dealer':
                    business_name = request.data.get('business_name')
                    if not business_name:
                        business_name = f"{user.first_name} {user.last_name}".strip() or username

                    DealerProfile.objects.create(
                        user=user,
                        business_name=business_name
                    )
                else:
                    CustomerProfile.objects.create(user=user)

                return self.ok(
                    UserSerializer(user).data,
                    "নিবন্ধন সফল",
                    status.HTTP_201_CREATED
                )

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except IntegrityError as e:
            logger.error(f"Registration integrity error: {e}")
            return self.fail({'database': 'ডেটাবেস ত্রুটি'}, "নিবন্ধন ব্যর্থ")
        except Exception as e:
            logger.exception(f"Registration error: {e}")
            return self.fail({'detail': 'অপ্রত্যাশিত ত্রুটি'}, "নিবন্ধন ব্যর্থ")


class CurrentUserView(BaseAPIView):
    """Get/Update current user"""

    def get(self, request):
        try:
            return self.ok(UserSerializer(request.user).data)
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return self.fail({'detail': str(e)}, "ব্যবহারকারীর তথ্য লোড ব্যর্থ")

    def patch(self, request):
        try:
            ser = UserSerializer(request.user, data=request.data, partial=True)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "প্রোফাইল আপডেট সফল")
            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Update user error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")


class UserListView(BaseAPIView):
    """Admin: List all users"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            qs = User.objects.all().order_by('id')
            return self.ok(UserSerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"User list error: {e}")
            return self.fail({'detail': str(e)}, "ব্যবহারকারী তালিকা লোড ব্যর্থ")


class UserDetailView(BaseAPIView):
    """Admin: Get specific user"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            user = get_object_or_404(User, pk=pk)
            return self.ok(UserSerializer(user).data)
        except Exception as e:
            logger.error(f"User detail error: {e}")
            return self.fail({'detail': str(e)}, "ব্যবহারকারী তথ্য লোড ব্যর্থ")


class GroupListView(BaseAPIView):
    """Admin: List groups"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            groups = Group.objects.all().order_by('name')
            return self.ok(GroupSerializer(groups, many=True).data)
        except Exception as e:
            logger.error(f"Group list error: {e}")
            return self.fail({'detail': str(e)}, "গ্রুপ তালিকা লোড ব্যর্থ")


# =============================================================================
# PROFILES
# =============================================================================

class CustomerProfileView(BaseAPIView):
    """Get/Update customer profile"""

    def get(self, request):
        try:
            prof = get_object_or_404(CustomerProfile, user=request.user)
            return self.ok(CustomerProfileSerializer(prof).data)
        except Exception as e:
            logger.error(f"Get customer profile error: {e}")
            return self.fail({'detail': str(e)}, "প্রোফাইল লোড ব্যর্থ")

    def patch(self, request):
        try:
            prof = get_object_or_404(CustomerProfile, user=request.user)
            ser = CustomerProfileSerializer(prof, data=request.data, partial=True)

            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "প্রোফাইল আপডেট সফল")
            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except DjangoValidationError as e:
            return self.fail({'validation': str(e)}, "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Update customer profile error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")


class DealerProfileView(BaseAPIView):
    """Get/Update dealer profile"""

    def get(self, request):
        try:
            prof = get_object_or_404(DealerProfile, user=request.user)
            return self.ok(DealerProfileSerializer(prof).data)
        except Exception as e:
            logger.error(f"Get dealer profile error: {e}")
            return self.fail({'detail': str(e)}, "প্রোফাইল লোড ব্যর্থ")

    def patch(self, request):
        try:
            prof = get_object_or_404(DealerProfile, user=request.user)
            ser = DealerProfileSerializer(prof, data=request.data, partial=True)

            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "প্রোফাইল আপডেট সফল")
            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except DjangoValidationError as e:
            return self.fail({'validation': str(e)}, "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Update dealer profile error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")


class DealerProfileListView(BaseAPIView):
    """List approved dealers"""

    def get(self, request):
        try:
            qs = DealerProfile.objects.filter(
                is_approved=True,
                is_active=True
            ).select_related('user').order_by('-created_at')

            # Optional filters
            city = self.q(request, 'city')
            if city:
                qs = qs.filter(city__icontains=city)

            return self.paginate(request, qs, DealerProfileSerializer)

        except Exception as e:
            logger.error(f"Dealer list error: {e}")
            return self.fail({'detail': str(e)}, "ডিলার তালিকা লোড ব্যর্থ")


class SubscriptionPlanListView(BaseAPIView):
    """List subscription plans"""

    def get(self, request):
        try:
            qs = SubscriptionPlan.objects.all().order_by('price')
            return self.ok(SubscriptionPlanSerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"Subscription plan list error: {e}")
            return self.fail({'detail': str(e)}, "সাবস্ক্রিপশন প্ল্যান লোড ব্যর্থ")


class SubscriptionPlanDetailView(BaseAPIView):
    """Get subscription plan details"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(SubscriptionPlan, pk=pk)
            return self.ok(SubscriptionPlanSerializer(obj).data)
        except Exception as e:
            logger.error(f"Subscription plan detail error: {e}")
            return self.fail({'detail': str(e)}, "সাবস্ক্রিপশন প্ল্যান লোড ব্যর্থ")


class CommissionHistoryListView(BaseAPIView):
    """Get commission history"""

    def get(self, request):
        try:
            if request.user.is_staff:
                qs = CommissionHistory.objects.all()
            elif hasattr(request.user, 'dealer_profile'):
                qs = CommissionHistory.objects.filter(dealer=request.user.dealer_profile)
            else:
                raise PermissionDenied("অনুমতি নেই")

            qs = qs.select_related('dealer', 'created_by').order_by('-created_at')
            return self.paginate(request, qs, CommissionHistorySerializer)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Commission history error: {e}")
            return self.fail({'detail': str(e)}, "কমিশন হিস্ট্রি লোড ব্যর্থ")


class CustomerVerificationListView(BaseAPIView):
    """Get customer verifications"""

    def get(self, request):
        try:
            qs = CustomerVerification.objects.filter(
                user=request.user
            ).order_by('-created_at')
            return self.ok(CustomerVerificationSerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"Customer verification list error: {e}")
            return self.fail({'detail': str(e)}, "ভেরিফিকেশন তালিকা লোড ব্যর্থ")


class DealerVerificationDocumentListView(BaseAPIView):
    """Get/Upload dealer verification documents"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = DealerVerificationDocument.objects.filter(
                dealer=request.user.dealer_profile
            ).select_related('reviewed_by').order_by('-uploaded_at')

            return self.ok(DealerVerificationDocumentSerializer(qs, many=True).data)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer document list error: {e}")
            return self.fail({'detail': str(e)}, "ডকুমেন্ট তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_dealer(request.user)

            # Validate required fields
            if 'document_type' not in request.data:
                return self.fail(
                    {'document_type': 'ডকুমেন্ট টাইপ প্রয়োজন'},
                    "ভ্যালিডেশন ত্রুটি"
                )

            if 'document_file' not in request.FILES:
                return self.fail(
                    {'document_file': 'ডকুমেন্ট ফাইল প্রয়োজন'},
                    "ভ্যালিডেশন ত্রুটি"
                )

            ser = DealerVerificationDocumentSerializer(data=request.data)
            if ser.is_valid():
                ser.save(dealer=request.user.dealer_profile)
                return self.ok(ser.data, "ডকুমেন্ট আপলোড সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer document upload error: {e}")
            return self.fail({'detail': str(e)}, "আপলোড ব্যর্থ")


# =============================================================================
# VEHICLES
# =============================================================================

class VehicleMakeListView(BaseAPIView):
    """List/Create vehicle makes"""

    def get(self, request):
        try:
            popular_only = self.q(request, 'popular_only')
            qs = VehicleMake.objects.all()

            if popular_only == 'true':
                qs = qs.filter(is_popular=True)

            qs = qs.order_by('-is_popular', 'name')
            return self.ok(VehicleMakeSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Vehicle make list error: {e}")
            return self.fail({'detail': str(e)}, "গাড়ির ব্র্যান্ড লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_admin(request.user)

            if not request.data.get('name'):
                return self.fail({'name': 'নাম প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            # Check duplicate
            if VehicleMake.objects.filter(name=request.data['name']).exists():
                return self.fail(
                    {'name': 'এই ব্র্যান্ড ইতিমধ্যে বিদ্যমান'},
                    "ডুপ্লিকেট এন্ট্রি"
                )

            ser = VehicleMakeSerializer(data=request.data)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "ব্র্যান্ড যোগ সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Vehicle make create error: {e}")
            return self.fail({'detail': str(e)}, "ব্র্যান্ড যোগ ব্যর্থ")


class VehicleMakeDetailView(BaseAPIView):
    """Get vehicle make details"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(VehicleMake, pk=pk)
            return self.ok(VehicleMakeSerializer(obj).data)
        except Exception as e:
            logger.error(f"Vehicle make detail error: {e}")
            return self.fail({'detail': str(e)}, "ব্র্যান্ড তথ্য লোড ব্যর্থ")


class VehicleModelListView(BaseAPIView):
    """List/Create vehicle models"""

    def get(self, request):
        try:
            make_id = self.q(request, 'make_id')
            qs = VehicleModel.objects.select_related('make')

            if make_id:
                if not make_id.isdigit():
                    return self.fail(
                        {'make_id': 'অবৈধ make_id'},
                        "ভ্যালিডেশন ত্রুটি"
                    )
                qs = qs.filter(make_id=make_id)

            qs = qs.order_by('make__name', 'name', 'year_from')
            return self.ok(VehicleModelSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Vehicle model list error: {e}")
            return self.fail({'detail': str(e)}, "গাড়ির মডেল লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_admin(request.user)

            required = ['make', 'name', 'year_from']
            validate_required_fields(request.data, required)

            ser = VehicleModelSerializer(data=request.data)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "মডেল যোগ সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Vehicle model create error: {e}")
            return self.fail({'detail': str(e)}, "মডেল যোগ ব্যর্থ")


class VehicleListCreateView(BaseAPIView):
    """List/Create customer vehicles"""

    def get(self, request):
        try:
            qs = Vehicle.objects.filter(
                owner=request.user,
                is_active=True
            ).select_related('make', 'model').order_by('-is_primary', '-created_at')

            return self.ok(VehicleSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Vehicle list error: {e}")
            return self.fail({'detail': str(e)}, "গাড়ির তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            required = ['make', 'model', 'year', 'license_plate', 'fuel_type']
            validate_required_fields(request.data, required)

            # Check duplicate license plate
            if Vehicle.objects.filter(license_plate=request.data['license_plate']).exists():
                return self.fail(
                    {'license_plate': 'এই নম্বর প্লেট ইতিমধ্যে নিবন্ধিত'},
                    "ডুপ্লিকেট এন্ট্রি"
                )

            with transaction.atomic():
                ser = VehicleSerializer(data=request.data)
                if ser.is_valid():
                    vehicle = ser.save(owner=request.user)

                    # Set as primary if it's the first vehicle
                    if not Vehicle.objects.filter(owner=request.user).exclude(pk=vehicle.pk).exists():
                        vehicle.is_primary = True
                        vehicle.save()

                    return self.ok(
                        VehicleSerializer(vehicle).data,
                        "গাড়ি যোগ সফল",
                        status.HTTP_201_CREATED
                    )

                return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Vehicle create error: {e}")
            return self.fail({'detail': str(e)}, "গাড়ি যোগ ব্যর্থ")


class VehicleDetailView(BaseAPIView):
    """Get/Update/Delete vehicle"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(Vehicle, pk=pk, owner=request.user)
            return self.ok(VehicleSerializer(obj).data)
        except Exception as e:
            logger.error(f"Vehicle detail error: {e}")
            return self.fail({'detail': str(e)}, "গাড়ির তথ্য লোড ব্যর্থ")

    def patch(self, request, pk):
        try:
            obj = get_object_or_404(Vehicle, pk=pk, owner=request.user)

            # Prevent duplicate license plate
            license_plate = request.data.get('license_plate')
            if license_plate and Vehicle.objects.filter(
                license_plate=license_plate
            ).exclude(pk=pk).exists():
                return self.fail(
                    {'license_plate': 'এই নম্বর প্লেট অন্য গাড়িতে ব্যবহৃত'},
                    "ডুপ্লিকেট এন্ট্রি"
                )

            ser = VehicleSerializer(obj, data=request.data, partial=True)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "গাড়ির তথ্য আপডেট সফল")

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except Exception as e:
            logger.error(f"Vehicle update error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")

    def delete(self, request, pk):
        try:
            obj = get_object_or_404(Vehicle, pk=pk, owner=request.user)
            obj.delete()
            return self.ok(message="গাড়ি মুছে ফেলা হয়েছে", status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Vehicle delete error: {e}")
            return self.fail({'detail': str(e)}, "মুছে ফেলা ব্যর্থ")


# =============================================================================
# SERVICES
# =============================================================================

class ServiceCategoryListView(BaseAPIView):
    """List/Create service categories"""

    def get(self, request):
        try:
            qs = ServiceCategory.objects.filter(is_active=True).order_by('sort_order', 'name')
            return self.ok(ServiceCategorySerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"Service category list error: {e}")
            return self.fail({'detail': str(e)}, "সার্ভিস ক্যাটাগরি লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_admin(request.user)

            if not request.data.get('name'):
                return self.fail({'name': 'নাম প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            ser = ServiceCategorySerializer(data=request.data)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "ক্যাটাগরি যোগ সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Service category create error: {e}")
            return self.fail({'detail': str(e)}, "ক্যাটাগরি যোগ ব্যর্থ")


class ServiceCategoryDetailView(BaseAPIView):
    """Get service category details"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(ServiceCategory, pk=pk)
            return self.ok(ServiceCategorySerializer(obj).data)
        except Exception as e:
            logger.error(f"Service category detail error: {e}")
            return self.fail({'detail': str(e)}, "ক্যাটাগরি তথ্য লোড ব্যর্থ")


class ServiceListView(BaseAPIView):
    """List all active services"""

    def get(self, request):
        try:
            qs = Service.objects.filter(is_active=True).select_related(
                'dealer', 'category'
            ).order_by('-is_featured', '-created_at')

            # Filters
            category_id = self.q(request, 'category_id')
            if category_id and category_id.isdigit():
                qs = qs.filter(category_id=category_id)

            dealer_id = self.q(request, 'dealer_id')
            if dealer_id and dealer_id.isdigit():
                qs = qs.filter(dealer_id=dealer_id)

            search = self.q(request, 'search')
            if search:
                qs = qs.filter(name__icontains=search)

            return self.paginate(request, qs, ServiceSerializer)

        except Exception as e:
            logger.error(f"Service list error: {e}")
            return self.fail({'detail': str(e)}, "সার্ভিস তালিকা লোড ব্যর্থ")


class ServiceDetailView(BaseAPIView):
    """Get service details"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(Service, pk=pk, is_active=True)

            # Increment view count
            Service.objects.filter(pk=pk).update(view_count=obj.view_count + 1)

            return self.ok(ServiceSerializer(obj).data)

        except Exception as e:
            logger.error(f"Service detail error: {e}")
            return self.fail({'detail': str(e)}, "সার্ভিস তথ্য লোড ব্যর্থ")


class DealerServiceListCreateView(BaseAPIView):
    """Dealer's own services"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = Service.objects.filter(dealer=request.user).select_related(
                'category'
            ).order_by('-created_at')

            return self.paginate(request, qs, ServiceSerializer)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer service list error: {e}")
            return self.fail({'detail': str(e)}, "সার্ভিস তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_dealer(request.user)

            required = ['category', 'name', 'description', 'base_price', 'estimated_duration']
            validate_required_fields(request.data, required)

            ser = ServiceSerializer(data=request.data)
            if ser.is_valid():
                ser.save(dealer=request.user)
                return self.ok(ser.data, "সার্ভিস যোগ সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer service create error: {e}")
            return self.fail({'detail': str(e)}, "সার্ভিস যোগ ব্যর্থ")


class DealerServiceDetailView(BaseAPIView):
    """Get/Update dealer's specific service"""

    def get(self, request, pk):
        try:
            ensure_dealer(request.user)
            obj = get_object_or_404(Service, pk=pk, dealer=request.user)
            return self.ok(ServiceSerializer(obj).data)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer service detail error: {e}")
            return self.fail({'detail': str(e)}, "সার্ভিস তথ্য লোড ব্যর্থ")

    def patch(self, request, pk):
        try:
            ensure_dealer(request.user)
            obj = get_object_or_404(Service, pk=pk, dealer=request.user)

            ser = ServiceSerializer(obj, data=request.data, partial=True)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "সার্ভিস আপডেট সফল")

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer service update error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")


class ServiceAddonListView(BaseAPIView):
    """List service addons"""

    def get(self, request):
        try:
            service_id = self.q(request, 'service_id')
            if not service_id:
                return self.fail({'service_id': 'service_id প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            if not service_id.isdigit():
                return self.fail({'service_id': 'অবৈধ service_id'}, "ভ্যালিডেশন ত্রুটি")

            qs = ServiceAddon.objects.filter(
                service_id=service_id,
                is_active=True
            ).order_by('name')

            return self.ok(ServiceAddonSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Service addon list error: {e}")
            return self.fail({'detail': str(e)}, "অ্যাডঅন তালিকা লোড ব্যর্থ")


class TechnicianListView(BaseAPIView):
    """List technicians"""

    def get(self, request):
        try:
            if hasattr(request.user, 'dealer_profile'):
                qs = Technician.objects.filter(dealer=request.user.dealer_profile)
            else:
                ensure_admin(request.user)
                qs = Technician.objects.all()

            qs = qs.order_by('name')
            return self.ok(TechnicianSerializer(qs, many=True).data)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Technician list error: {e}")
            return self.fail({'detail': str(e)}, "টেকনিশিয়ান তালিকা লোড ব্যর্থ")


class TechnicianDetailView(BaseAPIView):
    """Get technician details"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(Technician, pk=pk)

            # Check permission
            if hasattr(request.user, 'dealer_profile'):
                if obj.dealer != request.user.dealer_profile:
                    raise PermissionDenied("অনুমতি নেই")
            elif not request.user.is_staff:
                raise PermissionDenied("অনুমতি নেই")

            return self.ok(TechnicianSerializer(obj).data)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Technician detail error: {e}")
            return self.fail({'detail': str(e)}, "টেকনিশিয়ান তথ্য লোড ব্যর্থ")


class ServiceSlotListView(BaseAPIView):
    """List available service slots"""

    def get(self, request):
        try:
            service_id = self.q(request, 'service_id')
            date = self.q(request, 'date')

            qs = ServiceSlot.objects.filter(is_active=True).select_related('service')

            if service_id and service_id.isdigit():
                qs = qs.filter(service_id=service_id)

            if date:
                qs = qs.filter(date=date)

            # Only future slots
            qs = qs.filter(date__gte=timezone.now().date()).order_by('date', 'start_time')

            return self.ok(ServiceSlotSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Service slot list error: {e}")
            return self.fail({'detail': str(e)}, "স্লট তালিকা লোড ব্যর্থ")


class DealerSlotListCreateView(BaseAPIView):
    """Dealer's slots"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = ServiceSlot.objects.filter(
                service__dealer=request.user
            ).select_related('service').order_by('-date', '-start_time')

            return self.paginate(request, qs, ServiceSlotSerializer)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer slot list error: {e}")
            return self.fail({'detail': str(e)}, "স্লট তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_dealer(request.user)

            required = ['service', 'date', 'start_time', 'end_time']
            validate_required_fields(request.data, required)

            # Verify service belongs to dealer
            service_id = request.data.get('service')
            if not Service.objects.filter(id=service_id, dealer=request.user).exists():
                return self.fail({'service': 'অবৈধ সার্ভিস'}, "ভ্যালিডেশন ত্রুটি")

            ser = ServiceSlotSerializer(data=request.data)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "স্লট যোগ সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer slot create error: {e}")
            return self.fail({'detail': str(e)}, "স্লট যোগ ব্যর্থ")


class DealerSlotDetailView(BaseAPIView):
    """Get/Update dealer's specific slot"""

    def get(self, request, pk):
        try:
            ensure_dealer(request.user)
            obj = get_object_or_404(ServiceSlot, pk=pk, service__dealer=request.user)
            return self.ok(ServiceSlotSerializer(obj).data)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer slot detail error: {e}")
            return self.fail({'detail': str(e)}, "স্লট তথ্য লোড ব্যর্থ")

    def patch(self, request, pk):
        try:
            ensure_dealer(request.user)
            obj = get_object_or_404(ServiceSlot, pk=pk, service__dealer=request.user)

            ser = ServiceSlotSerializer(obj, data=request.data, partial=True)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "স্লট আপডেট সফল")

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer slot update error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")


# =============================================================================
# BOOKINGS
# =============================================================================

class CancellationPolicyListView(BaseAPIView):
    """List cancellation policies"""

    def get(self, request):
        try:
            qs = CancellationPolicy.objects.filter(is_active=True).order_by('name')
            return self.ok(CancellationPolicySerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"Cancellation policy list error: {e}")
            return self.fail({'detail': str(e)}, "পলিসি তালিকা লোড ব্যর্থ")


class PromotionListView(BaseAPIView):
    """List active promotions"""

    def get(self, request):
        try:
            now = timezone.now()
            qs = Promotion.objects.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).order_by('-created_at')

            return self.ok(PromotionSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Promotion list error: {e}")
            return self.fail({'detail': str(e)}, "প্রমোশন তালিকা লোড ব্যর্থ")


class PromotionValidateView(BaseAPIView):
    """Validate promotion code"""

    def post(self, request):
        try:
            code = request.data.get('code')
            if not code:
                return self.fail({'code': 'প্রমোশন কোড প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            now = timezone.now()
            try:
                promo = Promotion.objects.get(
                    code=code,
                    is_active=True,
                    start_date__lte=now,
                    end_date__gte=now
                )

                # Check max uses
                if promo.max_uses and promo.current_uses >= promo.max_uses:
                    return self.fail(
                        {'code': 'প্রমোশন কোড মেয়াদোত্তীর্ণ'},
                        "কোড অবৈধ"
                    )

                return self.ok(PromotionSerializer(promo).data, "প্রমোশন কোড বৈধ")

            except Promotion.DoesNotExist:
                return self.fail({'code': 'অবৈধ প্রমোশন কোড'}, "কোড অবৈধ")

        except Exception as e:
            logger.error(f"Promotion validate error: {e}")
            return self.fail({'detail': str(e)}, "ভ্যালিডেশন ব্যর্থ")


class BookingListCreateView(BaseAPIView):
    """List/Create bookings"""

    def get(self, request):
        try:
            if hasattr(request.user, 'dealer_profile'):
                qs = Booking.objects.filter(
                    service_slot__service__dealer=request.user
                ).select_related('customer', 'service_slot__service', 'vehicle')
            else:
                qs = Booking.objects.filter(customer=request.user).select_related(
                    'service_slot__service', 'vehicle'
                )

            # Filters
            status_filter = self.q(request, 'status')
            if status_filter:
                qs = qs.filter(status=status_filter)

            qs = qs.order_by('-created_at')
            return self.paginate(request, qs, BookingSerializer)

        except Exception as e:
            logger.error(f"Booking list error: {e}")
            return self.fail({'detail': str(e)}, "বুকিং তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            required = ['service_slot', 'vehicle']
            validate_required_fields(request.data, required)

            # Check slot availability
            slot_id = request.data.get('service_slot')
            try:
                slot = ServiceSlot.objects.get(id=slot_id)
                if not slot.is_active or slot.available_capacity <= 0:
                    return self.fail(
                        {'service_slot': 'এই স্লট উপলব্ধ নেই'},
                        "স্লট অনুপলব্ধ"
                    )
            except ServiceSlot.DoesNotExist:
                return self.fail({'service_slot': 'অবৈধ স্লট'}, "ভ্যালিডেশন ত্রুটি")

            # Check vehicle ownership
            vehicle_id = request.data.get('vehicle')
            if not Vehicle.objects.filter(id=vehicle_id, owner=request.user).exists():
                return self.fail({'vehicle': 'অবৈধ গাড়ি'}, "ভ্যালিডেশন ত্রুটি")

            with transaction.atomic():
                ser = BookingSerializer(data=request.data)
                if ser.is_valid():
                    booking = ser.save(customer=request.user)

                    # Decrease slot capacity
                    slot.available_capacity -= 1
                    slot.save()

                    return self.ok(
                        BookingSerializer(booking).data,
                        "বুকিং সফল",
                        status.HTTP_201_CREATED
                    )

                return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Booking create error: {e}")
            return self.fail({'detail': str(e)}, "বুকিং ব্যর্থ")


class BookingDetailView(BaseAPIView):
    """Get booking details"""

    def get(self, request, pk):
        try:
            if hasattr(request.user, 'dealer_profile'):
                obj = get_object_or_404(
                    Booking.objects.select_related('customer', 'service_slot__service', 'vehicle'),
                    pk=pk,
                    service_slot__service__dealer=request.user
                )
            else:
                obj = get_object_or_404(
                    Booking.objects.select_related('service_slot__service', 'vehicle'),
                    pk=pk,
                    customer=request.user
                )

            return self.ok(BookingSerializer(obj).data)

        except Exception as e:
            logger.error(f"Booking detail error: {e}")
            return self.fail({'detail': str(e)}, "বুকিং তথ্য লোড ব্যর্থ")


class BookingCancelView(BaseAPIView):
    """Cancel booking"""

    def post(self, request, pk):
        try:
            obj = get_object_or_404(Booking, pk=pk, customer=request.user)

            if obj.status not in ['pending', 'confirmed']:
                return self.fail(
                    {'status': f'"{obj.get_status_display()}" স্ট্যাটাসের বুকিং বাতিল করা যাবে না'},
                    "বাতিল করা সম্ভব নয়"
                )

            with transaction.atomic():
                obj.status = 'cancelled_by_customer'
                obj.cancellation_reason = request.data.get('reason', '')
                obj.save()

                # Increase slot capacity
                slot = obj.service_slot
                slot.available_capacity += 1
                slot.save()

                # Create status history
                BookingStatusHistory.objects.create(
                    booking=obj,
                    old_status=obj.status,
                    new_status='cancelled_by_customer',
                    changed_by=request.user,
                    reason=obj.cancellation_reason
                )

            return self.ok(BookingSerializer(obj).data, "বুকিং বাতিল সফল")

        except Exception as e:
            logger.error(f"Booking cancel error: {e}")
            return self.fail({'detail': str(e)}, "বাতিল ব্যর্থ")


class BookingConfirmView(BaseAPIView):
    """Dealer confirms booking"""

    def post(self, request, pk):
        try:
            ensure_dealer(request.user)
            obj = get_object_or_404(
                Booking,
                pk=pk,
                service_slot__service__dealer=request.user
            )

            if obj.status != 'pending':
                return self.fail(
                    {'status': 'শুধুমাত্র পেন্ডিং বুকিং নিশ্চিত করা যায়'},
                    "নিশ্চিতকরণ সম্ভব নয়"
                )

            with transaction.atomic():
                obj.status = 'confirmed'
                obj.save()

                # Create status history
                BookingStatusHistory.objects.create(
                    booking=obj,
                    old_status='pending',
                    new_status='confirmed',
                    changed_by=request.user
                )

            return self.ok(BookingSerializer(obj).data, "বুকিং নিশ্চিত সফল")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Booking confirm error: {e}")
            return self.fail({'detail': str(e)}, "নিশ্চিতকরণ ব্যর্থ")


class BookingAddonListView(BaseAPIView):
    """List booking addons"""

    def get(self, request):
        try:
            booking_id = self.q(request, 'booking_id')
            if not booking_id:
                return self.fail({'booking_id': 'booking_id প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            if not booking_id.isdigit():
                return self.fail({'booking_id': 'অবৈধ booking_id'}, "ভ্যালিডেশন ত্রুটি")

            qs = BookingAddon.objects.filter(
                booking_id=booking_id
            ).select_related('addon')

            return self.ok(BookingAddonSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Booking addon list error: {e}")
            return self.fail({'detail': str(e)}, "অ্যাডঅন তালিকা লোড ব্যর্থ")


class BookingStatusHistoryListView(BaseAPIView):
    """List booking status history"""

    def get(self, request):
        try:
            booking_id = self.q(request, 'booking_id')
            if not booking_id:
                return self.fail({'booking_id': 'booking_id প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            if not booking_id.isdigit():
                return self.fail({'booking_id': 'অবৈধ booking_id'}, "ভ্যালিডেশন ত্রুটি")

            qs = BookingStatusHistory.objects.filter(
                booking_id=booking_id
            ).select_related('changed_by').order_by('-created_at')

            return self.ok(BookingStatusHistorySerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Booking status history error: {e}")
            return self.fail({'detail': str(e)}, "স্ট্যাটাস হিস্ট্রি লোড ব্যর্থ")


# =============================================================================
# PAYMENTS / BALANCE
# =============================================================================

class VirtualCardListView(BaseAPIView):
    """List dealer's virtual cards"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = VirtualCard.objects.filter(dealer=request.user, is_active=True)
            return self.ok(VirtualCardSerializer(qs, many=True).data)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Virtual card list error: {e}")
            return self.fail({'detail': str(e)}, "কার্ড তালিকা লোড ব্যর্থ")


class PaymentListView(BaseAPIView):
    """List payments"""

    def get(self, request):
        try:
            if hasattr(request.user, 'dealer_profile'):
                qs = Payment.objects.filter(
                    booking__service_slot__service__dealer=request.user
                ).select_related('booking')
            else:
                qs = Payment.objects.filter(
                    booking__customer=request.user
                ).select_related('booking')

            qs = qs.order_by('-created_at')
            return self.paginate(request, qs, PaymentSerializer)

        except Exception as e:
            logger.error(f"Payment list error: {e}")
            return self.fail({'detail': str(e)}, "পেমেন্ট তালিকা লোড ব্যর্থ")


class PaymentDetailView(BaseAPIView):
    """Get payment details"""

    def get(self, request, pk):
        try:
            if hasattr(request.user, 'dealer_profile'):
                obj = get_object_or_404(
                    Payment,
                    pk=pk,
                    booking__service_slot__service__dealer=request.user
                )
            else:
                obj = get_object_or_404(Payment, pk=pk, booking__customer=request.user)

            return self.ok(PaymentSerializer(obj).data)

        except Exception as e:
            logger.error(f"Payment detail error: {e}")
            return self.fail({'detail': str(e)}, "পেমেন্ট তথ্য লোড ব্যর্থ")


class DealerPayoutListView(BaseAPIView):
    """List/Create dealer payouts"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = DealerPayout.objects.filter(dealer=request.user).order_by('-created_at')
            return self.paginate(request, qs, DealerPayoutSerializer)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer payout list error: {e}")
            return self.fail({'detail': str(e)}, "পেআউট তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            ensure_dealer(request.user)

            required = ['amount', 'bank_details']
            validate_required_fields(request.data, required)

            amount = request.data.get('amount')
            try:
                amount = float(amount)
                if amount <= 0:
                    return self.fail({'amount': 'পরিমাণ শূন্যের চেয়ে বেশি হতে হবে'}, "ভ্যালিডেশন ত্রুটি")
            except (ValueError, TypeError):
                return self.fail({'amount': 'অবৈধ পরিমাণ'}, "ভ্যালিডেশন ত্রুটি")

            # Check dealer balance
            dealer_profile = request.user.dealer_profile
            if dealer_profile.current_balance < amount:
                return self.fail(
                    {'amount': 'অপর্যাপ্ত ব্যালেন্স'},
                    "পেআউট অনুরোধ ব্যর্থ"
                )

            ser = DealerPayoutSerializer(data=request.data)
            if ser.is_valid():
                payout = ser.save(dealer=request.user)
                return self.ok(ser.data, "পেআউট অনুরোধ সফল", status.HTTP_201_CREATED)

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer payout create error: {e}")
            return self.fail({'detail': str(e)}, "পেআউট অনুরোধ ব্যর্থ")


class DealerPayoutDetailView(BaseAPIView):
    """Get dealer payout details"""

    def get(self, request, pk):
        try:
            ensure_dealer(request.user)
            obj = get_object_or_404(DealerPayout, pk=pk, dealer=request.user)
            return self.ok(DealerPayoutSerializer(obj).data)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer payout detail error: {e}")
            return self.fail({'detail': str(e)}, "পেআউট তথ্য লোড ব্যর্থ")


class BalanceTransactionListView(BaseAPIView):
    """List dealer balance transactions"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = BalanceTransaction.objects.filter(
                dealer=request.user.dealer_profile
            ).select_related('related_booking', 'related_payout').order_by('-created_at')

            return self.paginate(request, qs, BalanceTransactionSerializer)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Balance transaction list error: {e}")
            return self.fail({'detail': str(e)}, "ট্রানজেকশন তালিকা লোড ব্যর্থ")


# =============================================================================
# LOYALTY & REVIEWS
# =============================================================================

class LoyaltyTransactionListView(BaseAPIView):
    """List customer loyalty transactions"""

    def get(self, request):
        try:
            qs = LoyaltyTransaction.objects.filter(
                customer=request.user
            ).select_related('related_booking').order_by('-created_at')

            return self.paginate(request, qs, LoyaltyTransactionSerializer)

        except Exception as e:
            logger.error(f"Loyalty transaction list error: {e}")
            return self.fail({'detail': str(e)}, "লয়্যালটি ট্রানজেকশন লোড ব্যর্থ")


class ReviewListCreateView(BaseAPIView):
    """List/Create reviews"""

    def get(self, request):
        try:
            dealer_id = self.q(request, 'dealer_id')

            if dealer_id and dealer_id.isdigit():
                qs = Review.objects.filter(
                    dealer_id=dealer_id,
                    is_published=True
                ).select_related('customer', 'booking')
            else:
                qs = Review.objects.filter(customer=request.user).select_related('dealer', 'booking')

            qs = qs.order_by('-created_at')
            return self.paginate(request, qs, ReviewSerializer)

        except Exception as e:
            logger.error(f"Review list error: {e}")
            return self.fail({'detail': str(e)}, "রিভিউ তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            required = ['booking', 'overall_rating']
            validate_required_fields(request.data, required)

            booking_id = request.data.get('booking')

            # Verify booking exists and belongs to user
            try:
                booking = Booking.objects.select_related('service_slot__service__dealer').get(
                    id=booking_id,
                    customer=request.user
                )
            except Booking.DoesNotExist:
                return self.fail({'booking': 'অবৈধ বুকিং'}, "ভ্যালিডেশন ত্রুটি")

            # Check if booking is completed
            if booking.status != 'completed':
                return self.fail(
                    {'booking': 'শুধুমাত্র সম্পন্ন বুকিংয়ের জন্য রিভিউ দেয়া যাবে'},
                    "রিভিউ দেয়া সম্ভব নয়"
                )

            # Check if review already exists
            if Review.objects.filter(booking=booking).exists():
                return self.fail(
                    {'booking': 'এই বুকিংয়ের জন্য ইতিমধ্যে রিভিউ দেয়া হয়েছে'},
                    "ডুপ্লিকেট রিভিউ"
                )

            # Validate rating
            rating = request.data.get('overall_rating')
            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    return self.fail({'overall_rating': 'রেটিং ১-৫ এর মধ্যে হতে হবে'}, "ভ্যালিডেশন ত্রুটি")
            except (ValueError, TypeError):
                return self.fail({'overall_rating': 'অবৈধ রেটিং'}, "ভ্যালিডেশন ত্রুটি")

            with transaction.atomic():
                ser = ReviewSerializer(data=request.data)
                if ser.is_valid():
                    review = ser.save(
                        customer=request.user,
                        dealer=booking.service_slot.service.dealer
                    )
                    return self.ok(
                        ReviewSerializer(review).data,
                        "রিভিউ জমা সফল",
                        status.HTTP_201_CREATED
                    )

                return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Review create error: {e}")
            return self.fail({'detail': str(e)}, "রিভিউ জমা ব্যর্থ")


class ReviewDetailView(BaseAPIView):
    """Get review details"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(
                Review.objects.select_related('customer', 'dealer', 'booking'),
                pk=pk
            )
            return self.ok(ReviewSerializer(obj).data)
        except Exception as e:
            logger.error(f"Review detail error: {e}")
            return self.fail({'detail': str(e)}, "রিভিউ তথ্য লোড ব্যর্থ")


class ReviewRespondView(BaseAPIView):
    """Dealer responds to review"""

    def post(self, request, pk):
        try:
            ensure_dealer(request.user)

            review = get_object_or_404(Review, pk=pk, dealer=request.user)

            response = request.data.get('response', '').strip()
            if not response:
                return self.fail({'response': 'রেসপন্স প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            review.dealer_response = response
            review.dealer_response_date = timezone.now()
            review.save()

            return self.ok(ReviewSerializer(review).data, "রেসপন্স যোগ সফল")

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Review respond error: {e}")
            return self.fail({'detail': str(e)}, "রেসপন্স যোগ ব্যর্থ")


# =============================================================================
# NOTIFICATIONS
# =============================================================================

class NotificationListView(BaseAPIView):
    """List user notifications"""

    def get(self, request):
        try:
            unread_only = self.q(request, 'unread_only')

            qs = Notification.objects.filter(recipient=request.user)

            if unread_only == 'true':
                qs = qs.filter(read_at__isnull=True)

            qs = qs.order_by('-created_at')
            return self.paginate(request, qs, NotificationSerializer)

        except Exception as e:
            logger.error(f"Notification list error: {e}")
            return self.fail({'detail': str(e)}, "নোটিফিকেশন তালিকা লোড ব্যর্থ")


class NotificationMarkReadView(BaseAPIView):
    """Mark notification as read"""

    def post(self, request, pk):
        try:
            obj = get_object_or_404(Notification, pk=pk, recipient=request.user)

            if not obj.read_at:
                obj.read_at = timezone.now()
                obj.save()

            return self.ok(NotificationSerializer(obj).data, "পঠিত হিসেবে চিহ্নিত")

        except Exception as e:
            logger.error(f"Notification mark read error: {e}")
            return self.fail({'detail': str(e)}, "চিহ্নিতকরণ ব্যর্থ")


class NotificationTemplateListView(BaseAPIView):
    """List notification templates (Admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            qs = NotificationTemplate.objects.filter(is_active=True).order_by('name')
            return self.ok(NotificationTemplateSerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"Notification template list error: {e}")
            return self.fail({'detail': str(e)}, "টেমপ্লেট তালিকা লোড ব্যর্থ")


# =============================================================================
# SUPPORT
# =============================================================================

class SupportTicketListCreateView(BaseAPIView):
    """List/Create support tickets"""

    def get(self, request):
        try:
            qs = SupportTicket.objects.filter(
                user=request.user
            ).select_related('assigned_to').order_by('-created_at')

            return self.paginate(request, qs, SupportTicketSerializer)

        except Exception as e:
            logger.error(f"Support ticket list error: {e}")
            return self.fail({'detail': str(e)}, "টিকেট তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            required = ['subject', 'description', 'category']
            validate_required_fields(request.data, required)

            ser = SupportTicketSerializer(data=request.data)
            if ser.is_valid():
                ticket = ser.save(user=request.user)
                return self.ok(
                    SupportTicketSerializer(ticket).data,
                    "টিকেট তৈরি সফল",
                    status.HTTP_201_CREATED
                )

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Support ticket create error: {e}")
            return self.fail({'detail': str(e)}, "টিকেট তৈরি ব্যর্থ")


class SupportTicketDetailView(BaseAPIView):
    """Get/Update support ticket"""

    def get(self, request, pk):
        try:
            obj = get_object_or_404(
                SupportTicket.objects.select_related('assigned_to'),
                pk=pk,
                user=request.user
            )
            return self.ok(SupportTicketSerializer(obj).data)
        except Exception as e:
            logger.error(f"Support ticket detail error: {e}")
            return self.fail({'detail': str(e)}, "টিকেট তথ্য লোড ব্যর্থ")

    def patch(self, request, pk):
        try:
            obj = get_object_or_404(SupportTicket, pk=pk, user=request.user)

            # Only allow updating certain fields
            allowed_fields = ['description', 'priority']
            filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}

            if not filtered_data:
                return self.fail(
                    {'detail': 'কোন আপডেটযোগ্য ফিল্ড পাওয়া যায়নি'},
                    "ভ্যালিডেশন ত্রুটি"
                )

            ser = SupportTicketSerializer(obj, data=filtered_data, partial=True)
            if ser.is_valid():
                ser.save()
                return self.ok(ser.data, "টিকেট আপডেট সফল")

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except Exception as e:
            logger.error(f"Support ticket update error: {e}")
            return self.fail({'detail': str(e)}, "আপডেট ব্যর্থ")


class SupportMessageListCreateView(BaseAPIView):
    """List/Create support messages"""

    def get(self, request):
        try:
            ticket_id = self.q(request, 'ticket_id')
            if not ticket_id:
                return self.fail({'ticket_id': 'ticket_id প্রয়োজন'}, "ভ্যালিডেশন ত্রুটি")

            if not ticket_id.isdigit():
                return self.fail({'ticket_id': 'অবৈধ ticket_id'}, "ভ্যালিডেশন ত্রুটি")

            # Verify ticket belongs to user
            ticket = get_object_or_404(SupportTicket, pk=ticket_id, user=request.user)

            qs = SupportMessage.objects.filter(
                ticket=ticket
            ).select_related('sender').order_by('created_at')

            return self.ok(SupportMessageSerializer(qs, many=True).data)

        except Exception as e:
            logger.error(f"Support message list error: {e}")
            return self.fail({'detail': str(e)}, "মেসেজ তালিকা লোড ব্যর্থ")

    def post(self, request):
        try:
            required = ['ticket', 'message']
            validate_required_fields(request.data, required)

            ticket_id = request.data.get('ticket')

            # Verify ticket belongs to user
            ticket = get_object_or_404(SupportTicket, pk=ticket_id, user=request.user)

            if ticket.status == 'closed':
                return self.fail(
                    {'ticket': 'বন্ধ টিকেটে মেসেজ পাঠানো যাবে না'},
                    "মেসেজ পাঠানো সম্ভব নয়"
                )

            ser = SupportMessageSerializer(data=request.data)
            if ser.is_valid():
                message = ser.save(sender=request.user)
                return self.ok(
                    SupportMessageSerializer(message).data,
                    "মেসেজ পাঠানো হয়েছে",
                    status.HTTP_201_CREATED
                )

            return self.fail(ser.errors, "ভ্যালিডেশন ত্রুটি")

        except ValidationError as e:
            return self.fail(e.detail if hasattr(e, 'detail') else str(e), "ভ্যালিডেশন ত্রুটি")
        except Exception as e:
            logger.error(f"Support message create error: {e}")
            return self.fail({'detail': str(e)}, "মেসেজ পাঠানো ব্যর্থ")


# =============================================================================
# INTEGRATIONS / ANALYTICS / SYSTEM
# =============================================================================

class ExternalIntegrationListView(BaseAPIView):
    """List dealer integrations"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = ExternalIntegration.objects.filter(dealer=request.user).order_by('-created_at')
            return self.ok(ExternalIntegrationSerializer(qs, many=True).data)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"External integration list error: {e}")
            return self.fail({'detail': str(e)}, "ইন্টিগ্রেশন তালিকা লোড ব্যর্থ")


class WebhookEventListView(BaseAPIView):
    """List webhook events"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = WebhookEvent.objects.filter(dealer=request.user).order_by('-created_at')
            return self.paginate(request, qs, WebhookEventSerializer)
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Webhook event list error: {e}")
            return self.fail({'detail': str(e)}, "ওয়েবহুক ইভেন্ট লোড ব্যর্থ")


class SyncLogListView(BaseAPIView):
    """List sync logs"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = SyncLog.objects.filter(
                integration__dealer=request.user
            ).select_related('integration').order_by('-created_at')

            return self.paginate(request, qs, SyncLogSerializer)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Sync log list error: {e}")
            return self.fail({'detail': str(e)}, "সিঙ্ক লগ লোড ব্যর্থ")


class BookingAnalyticsListView(BaseAPIView):
    """List booking analytics (Admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            qs = BookingAnalytics.objects.all().order_by('-date')

            # Date filter
            from_date = self.q(request, 'from_date')
            to_date = self.q(request, 'to_date')

            if from_date:
                qs = qs.filter(date__gte=from_date)
            if to_date:
                qs = qs.filter(date__lte=to_date)

            return self.paginate(request, qs, BookingAnalyticsSerializer)

        except Exception as e:
            logger.error(f"Booking analytics list error: {e}")
            return self.fail({'detail': str(e)}, "অ্যানালিটিক্স লোড ব্যর্থ")


class DealerAnalyticsListView(BaseAPIView):
    """List dealer analytics"""

    def get(self, request):
        try:
            ensure_dealer(request.user)
            qs = DealerAnalytics.objects.filter(dealer=request.user).order_by('-date')

            # Date filter
            from_date = self.q(request, 'from_date')
            to_date = self.q(request, 'to_date')

            if from_date:
                qs = qs.filter(date__gte=from_date)
            if to_date:
                qs = qs.filter(date__lte=to_date)

            return self.paginate(request, qs, DealerAnalyticsSerializer)

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Dealer analytics list error: {e}")
            return self.fail({'detail': str(e)}, "অ্যানালিটিক্স লোড ব্যর্থ")


class SystemConfigurationListView(BaseAPIView):
    """List system configurations (Admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            qs = SystemConfiguration.objects.all().order_by('key')
            return self.ok(SystemConfigurationSerializer(qs, many=True).data)
        except Exception as e:
            logger.error(f"System configuration list error: {e}")
            return self.fail({'detail': str(e)}, "কনফিগারেশন লোড ব্যর্থ")


class AdminActionListView(BaseAPIView):
    """List admin actions (Admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            qs = AdminAction.objects.select_related('admin_user').order_by('-created_at')

            # Filter by action type
            action_type = self.q(request, 'action_type')
            if action_type:
                qs = qs.filter(action_type=action_type)

            return self.paginate(request, qs, AdminActionSerializer)

        except Exception as e:
            logger.error(f"Admin action list error: {e}")
            return self.fail({'detail': str(e)}, "অ্যাডমিন অ্যাকশন লোড ব্যর্থ")