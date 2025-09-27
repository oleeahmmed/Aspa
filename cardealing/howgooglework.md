# =============================================================================
# COMPLETE GOOGLE AUTHENTICATION FLOW
# =============================================================================

# ===== 1. CUSTOM SERIALIZERS (cardealing/api/serializers.py তে add করুন) =====
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from django.contrib.auth.models import User
from cardealing.models import CustomerProfile, DealerProfile

class CustomUserDetailsSerializer(UserDetailsSerializer):
    """User details with profile info for mobile"""
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
    """Registration with profile type"""
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

# ===== 2. CUSTOM SOCIAL AUTH VIEWS (cardealing/api/views.py তে add করুন) =====
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

class CustomGoogleLoginView(SocialLoginView):
    """Custom Google login with profile creation"""
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:8000/dj-rest-auth/google/callback/'
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

# ===== 3. URLs CONFIGURATION (cardealing/api/urls.py তে add করুন) =====
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomGoogleLoginView, CustomFacebookLoginView, create_dealer_profile

urlpatterns = [
    # Standard dj-rest-auth endpoints
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # JWT token refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom social auth
    path('auth/google/', CustomGoogleLoginView.as_view(), name='google_login'),
    path('auth/facebook/', CustomFacebookLoginView.as_view(), name='facebook_login'),
    
    # Profile management
    path('auth/create-dealer-profile/', create_dealer_profile, name='create_dealer_profile'),
    
    # Your existing API endpoints
    path('', include(router.urls)),
]
"""

# ===== 4. ANDROID IMPLEMENTATION EXAMPLE =====
"""
// AndroidManifest.xml
<uses-permission android:name="android.permission.INTERNET" />

// app/build.gradle
dependencies {
    implementation 'com.google.android.gms:play-services-auth:20.7.0'
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'
}

// AuthRepository.kt
class AuthRepository {
    private val apiService = RetrofitClient.apiService
    
    suspend fun googleSignIn(accessToken: String): AuthResponse {
        val request = GoogleAuthRequest(accessToken)
        return apiService.googleLogin(request)
    }
    
    suspend fun emailRegister(
        email: String,
        password1: String,
        password2: String,
        firstName: String,
        lastName: String,
        userType: String = "customer"
    ): AuthResponse {
        val request = RegisterRequest(email, password1, password2, firstName, lastName, userType)
        return apiService.register(request)
    }
    
    suspend fun createDealerProfile(dealerData: DealerProfileRequest): ApiResponse {
        return apiService.createDealerProfile(dealerData)
    }
}

// Data classes
data class GoogleAuthRequest(
    val access_token: String
)

data class RegisterRequest(
    val email: String,
    val password1: String,
    val password2: String,
    val first_name: String,
    val last_name: String,
    val user_type: String
)

data class AuthResponse(
    val access_token: String,
    val refresh_token: String,
    val user: UserData
)

data class UserData(
    val id: Int,
    val username: String,
    val email: String,
    val first_name: String,
    val last_name: String,
    val profile_type: String,
    val profile_id: Int?
)

// MainActivity.kt - Google Sign In
class MainActivity : AppCompatActivity() {
    
    private lateinit var googleSignInClient: GoogleSignInClient
    private lateinit var authRepository: AuthRepository
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        authRepository = AuthRepository()
        
        // Configure Google Sign In
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestServerAuthCode("YOUR_GOOGLE_CLIENT_ID") // আপনার Google Client ID
            .requestEmail()
            .build()
            
        googleSignInClient = GoogleSignIn.getClient(this, gso)
        
        findViewById<Button>(R.id.btnGoogleSignIn).setOnClickListener {
            signInWithGoogle()
        }
        
        findViewById<Button>(R.id.btnEmailRegister).setOnClickListener {
            registerWithEmail()
        }
    }
    
    private fun signInWithGoogle() {
        val signInIntent = googleSignInClient.signInIntent
        startActivityForResult(signInIntent, GOOGLE_SIGN_IN_REQUEST_CODE)
    }
    
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        
        if (requestCode == GOOGLE_SIGN_IN_REQUEST_CODE) {
            val task = GoogleSignIn.getSignedInAccountFromIntent(data)
            handleGoogleSignInResult(task)
        }
    }
    
    private fun handleGoogleSignInResult(completedTask: Task<GoogleSignInAccount>) {
        try {
            val account = completedTask.getResult(ApiException::class.java)
            val serverAuthCode = account?.serverAuthCode
            
            if (serverAuthCode != null) {
                // Send server auth code to your API
                lifecycleScope.launch {
                    try {
                        val response = authRepository.googleSignIn(serverAuthCode)
                        handleAuthSuccess(response)
                    } catch (e: Exception) {
                        handleAuthError(e)
                    }
                }
            }
        } catch (e: ApiException) {
            handleAuthError(e)
        }
    }
    
    private fun registerWithEmail() {
        lifecycleScope.launch {
            try {
                val response = authRepository.emailRegister(
                    email = "user@example.com",
                    password1 = "password123",
                    password2 = "password123",
                    firstName = "John",
                    lastName = "Doe",
                    userType = "customer"
                )
                handleAuthSuccess(response)
            } catch (e: Exception) {
                handleAuthError(e)
            }
        }
    }
    
    private fun handleAuthSuccess(response: AuthResponse) {
        // Save tokens
        TokenManager.saveTokens(response.access_token, response.refresh_token)
        
        // Check user type and navigate accordingly
        when (response.user.profile_type) {
            "customer" -> {
                // Navigate to customer dashboard
                startActivity(Intent(this, CustomerDashboardActivity::class.java))
            }
            "dealer" -> {
                if (response.user.profile_id == null) {
                    // Show dealer profile creation screen
                    startActivity(Intent(this, CreateDealerProfileActivity::class.java))
                } else {
                    // Navigate to dealer dashboard
                    startActivity(Intent(this, DealerDashboardActivity::class.java))
                }
            }
            else -> {
                // Handle unknown profile type
                showProfileTypeSelection()
            }
        }
        
        finish()
    }
    
    private fun showProfileTypeSelection() {
        // Show dialog to select customer or dealer
        AlertDialog.Builder(this)
            .setTitle("Select Account Type")
            .setItems(arrayOf("Customer", "Dealer")) { _, which ->
                when (which) {
                    0 -> {
                        // Create customer profile (already done by default)
                        startActivity(Intent(this, CustomerDashboardActivity::class.java))
                    }
                    1 -> {
                        // Navigate to dealer profile creation
                        startActivity(Intent(this, CreateDealerProfileActivity::class.java))
                    }
                }
                finish()
            }
            .show()
    }
    
    private fun handleAuthError(error: Exception) {
        Toast.makeText(this, "Authentication failed: ${error.message}", Toast.LENGTH_SHORT).show()
    }
    
    companion object {
        const val GOOGLE_SIGN_IN_REQUEST_CODE = 9001
    }
}

// TokenManager.kt
object TokenManager {
    private const val PREFS_NAME = "auth_prefs"
    private const val ACCESS_TOKEN_KEY = "access_token"
    private const val REFRESH_TOKEN_KEY = "refresh_token"
    
    fun saveTokens(accessToken: String, refreshToken: String) {
        val prefs = MyApplication.instance.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(ACCESS_TOKEN_KEY, accessToken)
            .putString(REFRESH_TOKEN_KEY, refreshToken)
            .apply()
    }
    
    fun getAccessToken(): String? {
        val prefs = MyApplication.instance.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(ACCESS_TOKEN_KEY, null)
    }
    
    fun clearTokens() {
        val prefs = MyApplication.instance.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().clear().apply()
    }
}

// ApiService.kt
interface ApiService {
    @POST("api/v1/auth/google/")
    suspend fun googleLogin(@Body request: GoogleAuthRequest): AuthResponse
    
    @POST("api/v1/auth/registration/")
    suspend fun register(@Body request: RegisterRequest): AuthResponse
    
    @POST("api/v1/auth/create-dealer-profile/")
    suspend fun createDealerProfile(@Body request: DealerProfileRequest): ApiResponse
    
    @POST("api/v1/auth/token/refresh/")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): TokenResponse
}
"""

# ===== 5. iOS SWIFT IMPLEMENTATION =====
"""
// AuthService.swift
import GoogleSignIn

class AuthService {
    static let shared = AuthService()
    private let baseURL = "http://127.0.0.1:8000/api/v1"
    
    func configureGoogleSignIn() {
        guard let path = Bundle.main.path(forResource: "GoogleService-Info", ofType: "plist"),
              let plist = NSDictionary(contentsOfFile: path),
              let clientId = plist["CLIENT_ID"] as? String else {
            fatalError("GoogleService-Info.plist not found")
        }
        
        GIDSignIn.sharedInstance.configuration = GIDConfiguration(clientID: clientId)
    }
    
    func signInWithGoogle() async throws -> AuthResponse {
        guard let presentingViewController = UIApplication.shared.windows.first?.rootViewController else {
            throw AuthError.noViewController
        }
        
        let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presentingViewController)
        
        guard let serverAuthCode = result.user.serverAuthCode else {
            throw AuthError.noServerAuthCode
        }
        
        return try await sendGoogleAuthToServer(serverAuthCode: serverAuthCode)
    }
    
    private func sendGoogleAuthToServer(serverAuthCode: String) async throws -> AuthResponse {
        let url = URL(string: "\(baseURL)/auth/google/")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = GoogleAuthRequest(accessToken: serverAuthCode)
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(AuthResponse.self, from: data)
    }
    
    func register(email: String, password: String, firstName: String, lastName: String, userType: String = "customer") async throws -> AuthResponse {
        let url = URL(string: "\(baseURL)/auth/registration/")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = RegisterRequest(
            email: email,
            password1: password,
            password2: password,
            firstName: firstName,
            lastName: lastName,
            userType: userType
        )
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(AuthResponse.self, from: data)
    }
}

// Models
struct GoogleAuthRequest: Codable {
    let accessToken: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
    }
}

struct RegisterRequest: Codable {
    let email: String
    let password1: String
    let password2: String
    let firstName: String
    let lastName: String
    let userType: String
    
    enum CodingKeys: String, CodingKey {
        case email, password1, password2
        case firstName = "first_name"
        case lastName = "last_name"
        case userType = "user_type"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let user: UserData
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case user
    }
}

// Usage in ViewController
class LoginViewController: UIViewController {
    
    override func viewDidLoad() {
        super.viewDidLoad()
        AuthService.shared.configureGoogleSignIn()
    }
    
    @IBAction func googleSignInTapped(_ sender: UIButton) {
        Task {
            do {
                let response = try await AuthService.shared.signInWithGoogle()
                await handleAuthSuccess(response)
            } catch {
                await handleAuthError(error)
            }
        }
    }
    
    @MainActor
    private func handleAuthSuccess(_ response: AuthResponse) {
        TokenManager.shared.saveTokens(
            accessToken: response.accessToken,
            refreshToken: response.refreshToken
        )
        
        switch response.user.profileType {
        case "customer":
            // Navigate to customer dashboard
            navigateToCustomerDashboard()
        case "dealer":
            if response.user.profileId == nil {
                // Navigate to dealer profile creation
                navigateToDealerProfileCreation()
            } else {
                // Navigate to dealer dashboard
                navigateToDealerDashboard()
            }
        default:
            // Show profile type selection
            showProfileTypeSelection()
        }
    }
}
"""

# ===== 6. ADMIN PANEL SETUP =====
"""
1. Django Admin থেকে Sites configure করুন:
   - Domain: 127.0.0.1:8000
   - Display name: Car Service

2. Social Applications add করুন:
   
   For Google:
   - Provider: Google
   - Name: Google OAuth2
   - Client id: YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
   - Secret key: YOUR_GOOGLE_CLIENT_SECRET
   - Sites: Select your configured site

   For Facebook:
   - Provider: Facebook
   - Name: Facebook Login
   - Client id: YOUR_FACEBOOK_APP_ID
   - Secret key: YOUR_FACEBOOK_APP_SECRET
   - Sites: Select your configured site
"""

# ===== 7. TESTING THE FLOW =====
"""
1. Start Django server: python manage.py runserver

2. Test Google auth with Postman:
   POST http://127.0.0.1:8000/api/v1/auth/google/
   Body: {
     "access_token": "GOOGLE_SERVER_AUTH_CODE"
   }

3. Expected Response:
   {
     "access_token": "jwt_access_token_here",
     "refresh_token": "jwt_refresh_token_here", 
     "user": {
       "id": 1,
       "username": "user@gmail.com",
       "email": "user@gmail.com",
       "first_name": "John",
       "last_name": "Doe",
       "profile_type": "customer",
       "profile_id": 1
     }
   }
"""