from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import *

# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom view to allow login with either username or email with enhanced response"""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            return Response({
                'refresh': data['refresh'],
                'access': data['access'],
                'user': data['user'],
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Login failed. Please check your credentials.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class UserRegistrationView(APIView):
    """User registration"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        user_type = request.data.get('user_type', 'customer')
        
        if not username or not email or not password:
            return Response(
                {'error': 'Username, email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )
        
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
        
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CurrentUserView(APIView):
    """Get/Update current user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):
    """List all users (Admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class UserDetailView(APIView):
    """User detail (Admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

class GroupListView(APIView):
    """List all groups"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

# =============================================================================
# PROFILE VIEWS
# =============================================================================

class CustomerProfileView(APIView):
    """Customer profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = CustomerProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = CustomerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DealerProfileView(APIView):
    """Dealer profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile = get_object_or_404(DealerProfile, user=request.user)
        serializer = DealerProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self, request):
        profile = get_object_or_404(DealerProfile, user=request.user)
        serializer = DealerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DealerProfileListView(APIView):
    """List all dealer profiles"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        dealers = DealerProfile.objects.filter(is_approved=True, is_active=True)
        serializer = DealerProfileSerializer(dealers, many=True)
        return Response(serializer.data)

class SubscriptionPlanListView(APIView):
    """List all subscription plans"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

class SubscriptionPlanDetailView(APIView):
    """Subscription plan detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        serializer = SubscriptionPlanSerializer(plan)
        return Response(serializer.data)

class CommissionHistoryListView(APIView):
    """Commission history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.is_staff:
            history = CommissionHistory.objects.all()
        elif hasattr(request.user, 'dealer_profile'):
            history = CommissionHistory.objects.filter(dealer=request.user.dealer_profile)
        else:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommissionHistorySerializer(history, many=True)
        return Response(serializer.data)

class CustomerVerificationListView(APIView):
    """Customer verifications"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        verifications = CustomerVerification.objects.filter(user=request.user)
        serializer = CustomerVerificationSerializer(verifications, many=True)
        return Response(serializer.data)

class DealerVerificationDocumentListView(APIView):
    """Dealer verification documents"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if hasattr(request.user, 'dealer_profile'):
            documents = DealerVerificationDocument.objects.filter(dealer=request.user.dealer_profile)
        else:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DealerVerificationDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DealerVerificationDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dealer=request.user.dealer_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LoginView(APIView):
    """Login with email or username - Returns JWT tokens"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

# =============================================================================
# VEHICLE VIEWS
# =============================================================================

class VehicleMakeListView(APIView):
    """List all vehicle makes"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        makes = VehicleMake.objects.all()
        serializer = VehicleMakeSerializer(makes, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VehicleMakeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleMakeDetailView(APIView):
    """Vehicle make detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        make = get_object_or_404(VehicleMake, pk=pk)
        serializer = VehicleMakeSerializer(make)
        return Response(serializer.data)


class VehicleModelListView(APIView):
    """List vehicle models"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        make_id = request.query_params.get('make_id')
        if make_id:
            models = VehicleModel.objects.filter(make_id=make_id)
        else:
            models = VehicleModel.objects.all()
        serializer = VehicleModelSerializer(models, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VehicleModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleListCreateView(APIView):
    """List and create vehicles"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user)
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = VehicleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleDetailView(APIView):
    """Vehicle detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data)
    
    def patch(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
        serializer = VehicleSerializer(vehicle, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
        vehicle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# SERVICE VIEWS
# =============================================================================

class ServiceCategoryListView(APIView):
    """List service categories"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        categories = ServiceCategory.objects.filter(is_active=True)
        serializer = ServiceCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ServiceCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceCategoryDetailView(APIView):
    """Service category detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        category = get_object_or_404(ServiceCategory, pk=pk)
        serializer = ServiceCategorySerializer(category)
        return Response(serializer.data)


class ServiceListView(APIView):
    """List services"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        services = Service.objects.filter(is_active=True)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


class ServiceDetailView(APIView):
    """Service detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceSerializer(service)
        return Response(serializer.data)


class DealerServiceListCreateView(APIView):
    """Dealer's services"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Dealer only'}, status=status.HTTP_403_FORBIDDEN)
        
        services = Service.objects.filter(dealer=request.user)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Dealer only'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dealer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DealerServiceDetailView(APIView):
    """Dealer service detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        service = get_object_or_404(Service, pk=pk, dealer=request.user)
        serializer = ServiceSerializer(service)
        return Response(serializer.data)


class ServiceAddonListView(APIView):
    """Service addons"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        service_id = request.query_params.get('service_id')
        if service_id:
            addons = ServiceAddon.objects.filter(service_id=service_id)
        else:
            addons = ServiceAddon.objects.all()
        serializer = ServiceAddonSerializer(addons, many=True)
        return Response(serializer.data)


class TechnicianListView(APIView):
    """Technicians"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if hasattr(request.user, 'dealer_profile'):
            technicians = Technician.objects.filter(dealer=request.user.dealer_profile)
        else:
            technicians = Technician.objects.all()
        serializer = TechnicianSerializer(technicians, many=True)
        return Response(serializer.data)


class TechnicianDetailView(APIView):
    """Technician detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        technician = get_object_or_404(Technician, pk=pk)
        serializer = TechnicianSerializer(technician)
        return Response(serializer.data)


class ServiceSlotListView(APIView):
    """Service slots"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        slots = ServiceSlot.objects.filter(is_active=True)
        serializer = ServiceSlotSerializer(slots, many=True)
        return Response(serializer.data)


class DealerSlotListCreateView(APIView):
    """Dealer slots"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Dealer only'}, status=status.HTTP_403_FORBIDDEN)
        
        slots = ServiceSlot.objects.filter(service__dealer=request.user)
        serializer = ServiceSlotSerializer(slots, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Dealer only'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ServiceSlotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DealerSlotDetailView(APIView):
    """Dealer slot detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        slot = get_object_or_404(ServiceSlot, pk=pk, service__dealer=request.user)
        serializer = ServiceSlotSerializer(slot)
        return Response(serializer.data)


# =============================================================================
# BOOKING VIEWS
# =============================================================================

class CancellationPolicyListView(APIView):
    """Cancellation policies"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        policies = CancellationPolicy.objects.all()
        serializer = CancellationPolicySerializer(policies, many=True)
        return Response(serializer.data)


class PromotionListView(APIView):
    """Promotions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        promotions = Promotion.objects.filter(is_active=True)
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)


class PromotionValidateView(APIView):
    """Validate promotion"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Promotion code required'}, status=status.HTTP_400_BAD_REQUEST)
        
        promotion = get_object_or_404(Promotion, code=code, is_active=True)
        serializer = PromotionSerializer(promotion)
        return Response(serializer.data)


class BookingListCreateView(APIView):
    """Bookings"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if hasattr(request.user, 'dealer_profile'):
            bookings = Booking.objects.filter(service_slot__service__dealer=request.user)
        else:
            bookings = Booking.objects.filter(customer=request.user)
        
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingDetailView(APIView):
    """Booking detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if hasattr(request.user, 'dealer_profile'):
            booking = get_object_or_404(Booking, pk=pk, service_slot__service__dealer=request.user)
        else:
            booking = get_object_or_404(Booking, pk=pk, customer=request.user)
        
        serializer = BookingSerializer(booking)
        return Response(serializer.data)


class BookingCancelView(APIView):
    """Cancel booking"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, customer=request.user)
        if booking.status != 'pending':
            return Response({'error': 'Can only cancel pending bookings'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'cancelled'
        booking.save()
        
        return Response({'message': 'Booking cancelled'})


class BookingConfirmView(APIView):
    """Confirm booking"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, service_slot__service__dealer=request.user)
        if booking.status != 'pending':
            return Response({'error': 'Not in pending status'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'confirmed'
        booking.save()
        
        return Response({'message': 'Booking confirmed'})


class BookingAddonListView(APIView):
    """Booking addons"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        booking_id = request.query_params.get('booking_id')
        if not booking_id:
            return Response({'error': 'booking_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        addons = BookingAddon.objects.filter(booking_id=booking_id)
        serializer = BookingAddonSerializer(addons, many=True)
        return Response(serializer.data)


class BookingStatusHistoryListView(APIView):
    """Booking status history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        booking_id = request.query_params.get('booking_id')
        if not booking_id:
            return Response({'error': 'booking_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        history = BookingStatusHistory.objects.filter(booking_id=booking_id)
        serializer = BookingStatusHistorySerializer(history, many=True)
        return Response(serializer.data)


# =============================================================================
# PAYMENT VIEWS
# =============================================================================

class VirtualCardListView(APIView):
    """Virtual cards"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cards = VirtualCard.objects.filter(dealer=request.user, is_active=True)
        serializer = VirtualCardSerializer(cards, many=True)
        return Response(serializer.data)


class PaymentListView(APIView):
    """Payments"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if hasattr(request.user, 'dealer_profile'):
            payments = Payment.objects.filter(booking__service_slot__service__dealer=request.user)
        else:
            payments = Payment.objects.filter(booking__customer=request.user)
        
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentDetailView(APIView):
    """Payment detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if hasattr(request.user, 'dealer_profile'):
            payment = get_object_or_404(Payment, pk=pk, booking__service_slot__service__dealer=request.user)
        else:
            payment = get_object_or_404(Payment, pk=pk, booking__customer=request.user)
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)


class DealerPayoutListView(APIView):
    """Dealer payouts"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payouts = DealerPayout.objects.filter(dealer=request.user)
        serializer = DealerPayoutSerializer(payouts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = DealerPayoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dealer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DealerPayoutDetailView(APIView):
    """Payout detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        payout = get_object_or_404(DealerPayout, pk=pk, dealer=request.user)
        serializer = DealerPayoutSerializer(payout)
        return Response(serializer.data)


class BalanceTransactionListView(APIView):
    """Balance transactions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Dealer only'}, status=status.HTTP_403_FORBIDDEN)
        
        transactions = BalanceTransaction.objects.filter(dealer=request.user.dealer_profile)
        serializer = BalanceTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


# =============================================================================
# LOYALTY & REVIEW VIEWS
# =============================================================================

class LoyaltyTransactionListView(APIView):
    """Loyalty transactions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = LoyaltyTransaction.objects.filter(customer=request.user)
        serializer = LoyaltyTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class ReviewListCreateView(APIView):
    """Reviews"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        dealer_id = request.query_params.get('dealer_id')
        if dealer_id:
            reviews = Review.objects.filter(dealer_id=dealer_id, is_published=True)
        else:
            reviews = Review.objects.filter(customer=request.user)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            booking = Booking.objects.get(id=request.data['booking_id'])
            serializer.save(
                customer=request.user,
                dealer=booking.service_slot.service.dealer
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailView(APIView):
    """Review detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)


class ReviewRespondView(APIView):
    """Dealer response to review"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, dealer=request.user)
        
        review.dealer_response = request.data.get('response', '')
        review.dealer_response_date = timezone.now()
        review.save()
        
        return Response({'message': 'Response added'})


# =============================================================================
# NOTIFICATION VIEWS
# =============================================================================

class NotificationListView(APIView):
    """Notifications"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    """Mark as read"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.read_at = timezone.now()
        notification.save()
        return Response({'message': 'Marked as read'})


class NotificationTemplateListView(APIView):
    """Notification templates (Admin)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        templates = NotificationTemplate.objects.all()
        serializer = NotificationTemplateSerializer(templates, many=True)
        return Response(serializer.data)


# =============================================================================
# SUPPORT VIEWS
# =============================================================================

class SupportTicketListCreateView(APIView):
    """Support tickets"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user)
        serializer = SupportTicketSerializer(tickets, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SupportTicketSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupportTicketDetailView(APIView):
    """Ticket detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
        serializer = SupportTicketSerializer(ticket)
        return Response(serializer.data)
    
    def patch(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
        serializer = SupportTicketSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupportMessageListCreateView(APIView):
    """Support messages"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        ticket_id = request.query_params.get('ticket_id')
        if not ticket_id:
            return Response({'error': 'ticket_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket = get_object_or_404(SupportTicket, pk=ticket_id, user=request.user)
        messages = SupportMessage.objects.filter(ticket=ticket)
        serializer = SupportMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SupportMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# INTEGRATION VIEWS
# =============================================================================

class ExternalIntegrationListView(APIView):
    """External integrations"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not hasattr(request.user, 'dealer_profile'):
            return Response({'error': 'Dealer only'}, status=status.HTTP_403_FORBIDDEN)
        
        integrations = ExternalIntegration.objects.filter(dealer=request.user)
        serializer = ExternalIntegrationSerializer(integrations, many=True)
        return Response(serializer.data)


class WebhookEventListView(APIView):
    """Webhook events"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        events = WebhookEvent.objects.filter(dealer=request.user)
        serializer = WebhookEventSerializer(events, many=True)
        return Response(serializer.data)


class SyncLogListView(APIView):
    """Sync logs"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        logs = SyncLog.objects.filter(integration__dealer=request.user)
        serializer = SyncLogSerializer(logs, many=True)
        return Response(serializer.data)


# =============================================================================
# ANALYTICS VIEWS
# =============================================================================

class BookingAnalyticsListView(APIView):
    """Booking analytics (Admin)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        analytics = BookingAnalytics.objects.all()
        serializer = BookingAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)


class DealerAnalyticsListView(APIView):
    """Dealer analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        analytics = DealerAnalytics.objects.filter(dealer=request.user)
        serializer = DealerAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)


# =============================================================================
# SYSTEM VIEWS
# =============================================================================

class SystemConfigurationListView(APIView):
    """System configs (Admin)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        configs = SystemConfiguration.objects.all()
        serializer = SystemConfigurationSerializer(configs, many=True)
        return Response(serializer.data)


class AdminActionListView(APIView):
    """Admin actions"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        actions = AdminAction.objects.all()
        serializer = AdminActionSerializer(actions, many=True)
        return Response(serializer.data)