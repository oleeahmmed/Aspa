from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal

from ..models import *
from .serializers import *
from .permissions import *


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['-date_joined']
    
    class Meta:
        swagger_tags = ['Authentication']
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={200: UserSerializer()},
        tags=['Authentication']
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Update current user profile",
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        tags=['Authentication']
    )
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user groups and permissions
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering = ['name']
    
    class Meta:
        swagger_tags = ['Authentication']


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    class Meta:
        swagger_tags = ['Authentication']


# =============================================================================
# USER PROFILE VIEWS
# =============================================================================

class CustomerProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customer profiles
    """
    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['preferred_notification', 'city']
    search_fields = ['user__username', 'user__email', 'phone_number']
    ordering_fields = ['total_bookings', 'total_spent', 'loyalty_points', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Users & Profiles']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomerProfile.objects.all()
        return CustomerProfile.objects.filter(user=self.request.user)


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscription plans
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['featured_listing', 'priority_support', 'analytics_access']
    ordering_fields = ['price', 'commission_rate', 'created_at']
    ordering = ['price']
    
    class Meta:
        swagger_tags = ['Users & Profiles']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class DealerProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dealer profiles
    """
    queryset = DealerProfile.objects.all()
    serializer_class = DealerProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['business_type', 'is_approved', 'is_active', 'city']
    search_fields = ['business_name', 'user__username', 'business_phone']
    ordering_fields = ['rating', 'total_reviews', 'total_bookings', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Users & Profiles']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return DealerProfile.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return DealerProfile.objects.filter(user=self.request.user)
        return DealerProfile.objects.filter(is_approved=True, is_active=True)
    
    @swagger_auto_schema(
        operation_description="Approve dealer profile",
        responses={200: openapi.Response('Dealer approved successfully')},
        tags=['Users & Profiles']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve dealer profile"""
        dealer = self.get_object()
        dealer.is_approved = True
        dealer.save()
        
        # Log admin action
        AdminAction.objects.create(
            admin_user=request.user,
            action_type='dealer_approved',
            target_model='DealerProfile',
            target_id=dealer.id,
            description=f'Approved dealer: {dealer.business_name}'
        )
        
        return Response({'message': 'Dealer approved successfully'})


class CommissionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing commission history
    """
    queryset = CommissionHistory.objects.all()
    serializer_class = CommissionHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['dealer']
    ordering_fields = ['effective_date', 'commission_percentage', 'created_at']
    ordering = ['-effective_date']
    
    class Meta:
        swagger_tags = ['Users & Profiles']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return CommissionHistory.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return CommissionHistory.objects.filter(dealer=self.request.user.dealer_profile)
        return CommissionHistory.objects.none()


class CustomerVerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customer verifications
    """
    queryset = CustomerVerification.objects.all()
    serializer_class = CustomerVerificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user', 'verification_type', 'status']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Users & Profiles']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomerVerification.objects.all()
        return CustomerVerification.objects.filter(user=self.request.user)


class DealerVerificationDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dealer verification documents
    """
    queryset = DealerVerificationDocument.objects.all()
    serializer_class = DealerVerificationDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['dealer', 'document_type', 'status']
    ordering_fields = ['uploaded_at', 'reviewed_at']
    ordering = ['-uploaded_at']
    
    class Meta:
        swagger_tags = ['Users & Profiles']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return DealerVerificationDocument.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return DealerVerificationDocument.objects.filter(dealer=self.request.user.dealer_profile)
        return DealerVerificationDocument.objects.none()


# =============================================================================
# VEHICLE MANAGEMENT VIEWS
# =============================================================================

class VehicleMakeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicle makes
    """
    queryset = VehicleMake.objects.all()
    serializer_class = VehicleMakeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_popular']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    class Meta:
        swagger_tags = ['Vehicle Management']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class VehicleModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicle models
    """
    queryset = VehicleModel.objects.all()
    serializer_class = VehicleModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['make', 'year_from', 'year_to']
    search_fields = ['name', 'make__name']
    ordering_fields = ['name', 'year_from', 'created_at']
    ordering = ['make__name', 'name']
    
    class Meta:
        swagger_tags = ['Vehicle Management']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicles
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['make', 'model', 'fuel_type', 'transmission', 'is_primary', 'is_active']
    search_fields = ['license_plate', 'vin', 'color']
    ordering_fields = ['year', 'current_mileage', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Vehicle Management']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Vehicle.objects.all()
        return Vehicle.objects.filter(owner=self.request.user)


# =============================================================================
# SERVICE MANAGEMENT VIEWS
# =============================================================================

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing service categories
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'requires_vehicle_drop']
    search_fields = ['name', 'description']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']
    
    class Meta:
        swagger_tags = ['Service Management']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing services
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'service_location', 'is_featured', 'dealer']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['base_price', 'estimated_duration', 'total_bookings', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Service Management']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Service.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return Service.objects.filter(dealer=self.request.user)
        return Service.objects.filter(is_active=True)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsDealerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Search services by location and filters",
        manual_parameters=[
            openapi.Parameter('lat', openapi.IN_QUERY, description="Latitude", type=openapi.TYPE_NUMBER),
            openapi.Parameter('lng', openapi.IN_QUERY, description="Longitude", type=openapi.TYPE_NUMBER),
            openapi.Parameter('radius', openapi.IN_QUERY, description="Search radius in KM", type=openapi.TYPE_INTEGER),
        ],
        tags=['Service Management']
    )
    @action(detail=False, methods=['get'])
    def search_by_location(self, request):
        """Search services by location"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = int(request.query_params.get('radius', 10))
        
        if not lat or not lng:
            return Response({'error': 'Latitude and longitude are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # This would require a proper geospatial query in production
        # For now, we'll return all services
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ServiceAddonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing service addons
    """
    queryset = ServiceAddon.objects.filter(is_active=True)
    serializer_class = ServiceAddonSerializer
    permission_classes = [IsAuthenticated, IsDealerOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['service', 'is_required']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['service', 'name']
    
    class Meta:
        swagger_tags = ['Service Management']


class TechnicianViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing technicians
    """
    queryset = Technician.objects.all()
    serializer_class = TechnicianSerializer
    permission_classes = [IsAuthenticated, IsDealerOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['dealer', 'is_available']
    search_fields = ['name', 'phone_number']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    class Meta:
        swagger_tags = ['Service Management']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Technician.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return Technician.objects.filter(dealer=self.request.user.dealer_profile)
        return Technician.objects.none()


class ServiceSlotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing service slots
    """
    queryset = ServiceSlot.objects.filter(is_active=True)
    serializer_class = ServiceSlotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service', 'date', 'is_blocked', 'assigned_technician']
    ordering_fields = ['date', 'start_time', 'created_at']
    ordering = ['date', 'start_time']
    
    class Meta:
        swagger_tags = ['Service Management']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ServiceSlot.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return ServiceSlot.objects.filter(service__dealer=self.request.user)
        return ServiceSlot.objects.filter(is_active=True, available_capacity__gt=0)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsDealerOrAdmin]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Get available slots for a service",
        manual_parameters=[
            openapi.Parameter('service_id', openapi.IN_QUERY, description="Service ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Start date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="End date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        tags=['Service Management']
    )
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available slots for booking"""
        service_id = request.query_params.get('service_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset().filter(available_capacity__gt=0)
        
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# =============================================================================
# BOOKING SYSTEM VIEWS
# =============================================================================

class CancellationPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cancellation policies
    """
    queryset = CancellationPolicy.objects.filter(is_active=True)
    serializer_class = CancellationPolicySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_default']
    ordering_fields = ['free_cancellation_hours', 'created_at']
    ordering = ['name']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'service_location', 'source', 'customer']
    search_fields = ['booking_number', 'contact_name', 'contact_phone']
    ordering_fields = ['service_scheduled_at', 'total_amount', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return Booking.objects.filter(service_slot__service__dealer=self.request.user)
        return Booking.objects.filter(customer=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Cancel booking",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(type=openapi.TYPE_STRING, description='Cancellation reason')
            }
        ),
        tags=['Bookings & Payments']
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel booking"""
        booking = self.get_object()
        reason = request.data.get('reason', '')
        
        if booking.status not in ['pending', 'confirmed']:
            return Response({'error': 'Booking cannot be cancelled'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate cancellation fee
        cancellation_fee = booking.get_cancellation_fee()
        
        # Update booking status
        old_status = booking.status
        booking.status = 'cancelled_by_customer' if booking.customer == request.user else 'cancelled_by_dealer'
        booking.cancellation_reason = reason
        booking.save()
        
        # Create status history
        BookingStatusHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=booking.status,
            changed_by=request.user,
            reason=reason
        )
        
        return Response({
            'message': 'Booking cancelled successfully',
            'cancellation_fee': cancellation_fee
        })
    
    @swagger_auto_schema(
        operation_description="Confirm booking (dealer only)",
        tags=['Bookings & Payments']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDealerOrAdmin])
    def confirm(self, request, pk=None):
        """Confirm booking (dealer only)"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response({'error': 'Booking is not in pending status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        old_status = booking.status
        booking.status = 'confirmed'
        booking.save()
        
        # Create status history
        BookingStatusHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=booking.status,
            changed_by=request.user,
            reason='Confirmed by dealer'
        )
        
        return Response({'message': 'Booking confirmed successfully'})


class BookingAddonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing booking addons
    """
    queryset = BookingAddon.objects.all()
    serializer_class = BookingAddonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['booking', 'addon']
    ordering_fields = ['total_price', 'created_at']
    ordering = ['booking', 'addon']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']


class BookingStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing booking status history
    """
    queryset = BookingStatusHistory.objects.all()
    serializer_class = BookingStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['booking', 'new_status', 'changed_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return BookingStatusHistory.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return BookingStatusHistory.objects.filter(
                booking__service_slot__service__dealer=self.request.user
            )
        return BookingStatusHistory.objects.filter(booking__customer=self.request.user)


# =============================================================================
# PAYMENT SYSTEM VIEWS
# =============================================================================

class VirtualCardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing virtual cards
    """
    queryset = VirtualCard.objects.filter(is_active=True)
    serializer_class = VirtualCardSerializer
    permission_classes = [IsAuthenticated, IsDealerOrAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['dealer']
    ordering_fields = ['balance', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return VirtualCard.objects.all()
        return VirtualCard.objects.filter(dealer=self.request.user)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing payments
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'payment_method_type', 'booking']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return Payment.objects.filter(booking__service_slot__service__dealer=self.request.user)
        return Payment.objects.filter(booking__customer=self.request.user)


class DealerPayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dealer payouts
    """
    queryset = DealerPayout.objects.all()
    serializer_class = DealerPayoutSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'dealer']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return DealerPayout.objects.all()
        return DealerPayout.objects.filter(dealer=self.request.user)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Process payout (admin only)",
        tags=['Bookings & Payments']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def process(self, request, pk=None):
        """Process payout (admin only)"""
        payout = self.get_object()
        
        if payout.status != 'pending':
            return Response({'error': 'Payout is not in pending status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        payout.status = 'processing'
        payout.processed_by = request.user
        payout.processed_at = timezone.now()
        payout.save()
        
        return Response({'message': 'Payout processing initiated'})


class PayoutRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payout requests
    """
    queryset = PayoutRequest.objects.all()
    serializer_class = PayoutRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'dealer']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']


class BalanceTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing balance transactions
    """
    queryset = BalanceTransaction.objects.all()
    serializer_class = BalanceTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['transaction_type', 'dealer']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Bookings & Payments']


# =============================================================================
# COMMUNICATION VIEWS
# =============================================================================

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'channel', 'recipient']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Communication']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(recipient=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Mark notification as read",
        tags=['Communication']
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.read_at = timezone.now()
        notification.save()
        return Response({'message': 'Notification marked as read'})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification templates
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'is_active']
    search_fields = ['name', 'email_subject', 'email_body']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    class Meta:
        swagger_tags = ['Communication']


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews
    """
    queryset = Review.objects.filter(is_published=True)
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['overall_rating', 'dealer', 'is_verified']
    search_fields = ['title', 'comment']
    ordering_fields = ['overall_rating', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Communication']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return Review.objects.filter(dealer=self.request.user)
        return Review.objects.filter(is_published=True)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated, IsCustomer]
        elif self.action == 'respond':
            permission_classes = [IsAuthenticated, IsDealerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Respond to review (dealer only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'response': openapi.Schema(type=openapi.TYPE_STRING, description='Dealer response')
            }
        ),
        tags=['Communication']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDealerOrAdmin])
    def respond(self, request, pk=None):
        """Respond to review (dealer only)"""
        review = self.get_object()
        response_text = request.data.get('response', '')
        
        if not response_text:
            return Response({'error': 'Response text is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        review.dealer_response = response_text
        review.dealer_response_date = timezone.now()
        review.save()
        
        return Response({'message': 'Response added successfully'})


class PromotionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing promotions
    """
    queryset = Promotion.objects.filter(is_active=True)
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['promotion_type', 'target_audience']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Communication']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'validate_code']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Validate promotion code",
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY, description="Promotion code", type=openapi.TYPE_STRING, required=True),
        ],
        tags=['Communication']
    )
    @action(detail=False, methods=['get'])
    def validate_code(self, request):
        """Validate promotion code"""
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            promotion = Promotion.objects.get(
                code=code,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            
            # Check usage limits
            if promotion.max_uses and promotion.current_uses >= promotion.max_uses:
                return Response({'error': 'Promotion code has reached maximum usage'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(promotion)
            return Response(serializer.data)
            
        except Promotion.DoesNotExist:
            return Response({'error': 'Invalid or expired promotion code'}, 
                          status=status.HTTP_404_NOT_FOUND)


class LoyaltyTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing loyalty transactions
    """
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['transaction_type', 'customer']
    ordering_fields = ['points', 'created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Communication']


# =============================================================================
# SUPPORT SYSTEM VIEWS
# =============================================================================

class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing support tickets
    """
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'assigned_to']
    search_fields = ['ticket_number', 'subject', 'description']
    ordering_fields = ['priority', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Support System']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Assign ticket to staff member (admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'assigned_to': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID to assign to')
            }
        ),
        tags=['Support System']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def assign(self, request, pk=None):
        """Assign ticket to staff member"""
        ticket = self.get_object()
        assigned_to_id = request.data.get('assigned_to')
        
        try:
            assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
            ticket.assigned_to = assigned_user
            ticket.save()
            return Response({'message': 'Ticket assigned successfully'})
        except User.DoesNotExist:
            return Response({'error': 'Invalid staff user'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class SupportMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing support messages
    """
    queryset = SupportMessage.objects.all()
    serializer_class = SupportMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['ticket', 'sender', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    class Meta:
        swagger_tags = ['Support System']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return SupportMessage.objects.all()
        return SupportMessage.objects.filter(
            Q(ticket__user=self.request.user) | Q(sender=self.request.user)
        )


# =============================================================================
# INTEGRATIONS VIEWS
# =============================================================================

class ExternalIntegrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing external integrations
    """
    queryset = ExternalIntegration.objects.all()
    serializer_class = ExternalIntegrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['dealer', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    class Meta:
        swagger_tags = ['Integrations']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ExternalIntegration.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return ExternalIntegration.objects.filter(dealer=self.request.user)
        return ExternalIntegration.objects.none()


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing webhook events
    """
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['dealer', 'status', 'event_type']
    ordering_fields = ['created_at', 'processed_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Integrations']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return WebhookEvent.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return WebhookEvent.objects.filter(dealer=self.request.user)
        return WebhookEvent.objects.none()


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing sync logs
    """
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['integration', 'status', 'sync_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['Integrations']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return SyncLog.objects.all()
        elif hasattr(self.request.user, 'dealer_profile'):
            return SyncLog.objects.filter(integration__dealer=self.request.user)
        return SyncLog.objects.none()


# =============================================================================
# ANALYTICS VIEWS
# =============================================================================

class BookingAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing booking analytics
    """
    queryset = BookingAnalytics.objects.all()
    serializer_class = BookingAnalyticsSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'total_bookings', 'total_revenue']
    ordering = ['-date']
    
    class Meta:
        swagger_tags = ['Analytics']


class DealerAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing dealer analytics
    """
    queryset = DealerAnalytics.objects.all()
    serializer_class = DealerAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['dealer', 'date']
    ordering_fields = ['date', 'total_bookings', 'total_earnings']
    ordering = ['-date']
    
    class Meta:
        swagger_tags = ['Analytics']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return DealerAnalytics.objects.all()
        return DealerAnalytics.objects.filter(dealer=self.request.user)


# =============================================================================
# SYSTEM CONFIGURATION VIEWS
# =============================================================================

class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system configuration
    """
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['data_type']
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'created_at']
    ordering = ['key']
    
    class Meta:
        swagger_tags = ['System']


class AdminActionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing admin actions
    """
    queryset = AdminAction.objects.all()
    serializer_class = AdminActionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action_type', 'admin_user', 'target_model']
    search_fields = ['description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    class Meta:
        swagger_tags = ['System']



# =============================================================================
# MOBILE AUTHENTICATION VIEWS (ADD THESE TO YOUR EXISTING FILE)
# =============================================================================

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny



class CustomGoogleLoginView(SocialLoginView):
    """Custom Google login with profile creation"""
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:8000/api/v1/auth/google/callback/'
    client_class = None
    
    def get_response(self):
        response = super().get_response()
        
        # Add custom user data to response
        if hasattr(self, 'user'):
            # Create customer profile if doesn't exist (default)
            if not (hasattr(self.user, 'customer_profile') or hasattr(self.user, 'dealer_profile')):
                CustomerProfile.objects.get_or_create(user=self.user)
            
            # Add user details to response
            user_serializer = CustomUserDetailsSerializer(self.user)
            response.data['user'] = user_serializer.data
            
        return response

class CustomFacebookLoginView(SocialLoginView):
    """Custom Facebook login with profile creation"""
    adapter_class = FacebookOAuth2Adapter
    
    def get_response(self):
        response = super().get_response()
        
        if hasattr(self, 'user'):
            if not (hasattr(self.user, 'customer_profile') or hasattr(self.user, 'dealer_profile')):
                CustomerProfile.objects.get_or_create(user=self.user)
            
            user_serializer = CustomUserDetailsSerializer(self.user)
            response.data['user'] = user_serializer.data
            
        return response

class CustomAppleLoginView(SocialLoginView):
    """Custom Apple login with profile creation"""
    adapter_class = AppleOAuth2Adapter
    
    def get_response(self):
        response = super().get_response()
        
        if hasattr(self, 'user'):
            if not (hasattr(self.user, 'customer_profile') or hasattr(self.user, 'dealer_profile')):
                CustomerProfile.objects.get_or_create(user=self.user)
            
            user_serializer = CustomUserDetailsSerializer(self.user)
            response.data['user'] = user_serializer.data
            
        return response

@api_view(['POST'])
@permission_classes([AllowAny])
def create_dealer_profile(request):
    """Create dealer profile for existing user"""
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, 
                       status=status.HTTP_401_UNAUTHORIZED)
    
    user = request.user
    
    if hasattr(user, 'dealer_profile'):
        return Response({'error': 'Dealer profile already exists'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Create dealer profile
    DealerProfile.objects.create(
        user=user,
        business_name=request.data.get('business_name', f"{user.first_name} {user.last_name} Business"),
        address=request.data.get('address', 'To be updated'),
        city=request.data.get('city', 'To be updated'),
        postal_code=request.data.get('postal_code', '00000'),
        latitude=float(request.data.get('latitude', 0.0)),
        longitude=float(request.data.get('longitude', 0.0)),
        business_phone=request.data.get('business_phone', 'To be updated'),
        bank_account_name=request.data.get('bank_account_name', f"{user.first_name} {user.last_name}"),
        bank_account_number=request.data.get('bank_account_number', '0000000000'),
        bank_name=request.data.get('bank_name', 'To be updated'),
        bank_routing_number=request.data.get('bank_routing_number', '000000000')
    )
    
    user_serializer = CustomUserDetailsSerializer(user)
    return Response({
        'message': 'Dealer profile created successfully',
        'user': user_serializer.data
    })