from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Car Dealing API",
        default_version='v1',
        description="""
        Comprehensive Car Service Booking System API
        
        ## Authentication
        This API uses Token Authentication. Include the token in the Authorization header:
        `Authorization: Token your_token_here`
        
        ## API Organization
        The API is organized into the following main sections:
        
        ### Authentication
        - User management and authentication
        - Group and permission management
        
        ### Users & Profiles
        - Customer and dealer profile management
        - Subscription plans and commission tracking
        
        ### Vehicle Management
        - Vehicle makes, models, and customer vehicles
        
        ### Service Management
        - Service categories, services, and technicians
        - Service slots and availability management
        
        ### Bookings & Payments
        - Booking management and status tracking
        - Payment processing and payout management
        - Cancellation policies and promotions
        
        ### Communication
        - Notifications and reviews
        - Loyalty program management
        
        ### Support System
        - Support tickets and messaging
        
        ### Analytics
        - Booking and dealer performance analytics
        
        ### System
        - System configuration and admin actions
        
        ## Rate Limiting
        API requests are rate limited to prevent abuse.
        
        ## Error Handling
        The API returns standard HTTP status codes and JSON error responses.
        """,
        terms_of_service="https://www.yourcompany.com/terms/",
        contact=openapi.Contact(email="api@yourcompany.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('api/v1/', include('cardealing.api.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Allauth
    path('dj-rest-auth/', include('dj_rest_auth.urls')),  # REST auth
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),  # Social registration
    
    path('api/v1/', include('cardealing.api.urls')),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # path('__debug__/', include('debug_toolbar.urls')),  # Debug Toolbar
]

# Serve media/static in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
