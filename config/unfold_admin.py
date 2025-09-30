
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.utils.functional import lazy
from django.conf import settings

static_lazy = lazy(static, str)

def get_navigation_for_user(request):
    """Return navigation based on user type"""
    user = request.user
    
    # Complete navigation for all users
    return [
        {
            "title": _("Dashboard"),
            "separator": True,
            "items": [
                {
                    "title": _("Dashboard"),
                    "icon": "dashboard",
                    "link": "/admin/",
                },
            ],
        },
        {
            "title": _("Authentication"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Users"),
                    "icon": "people",
                    "link": "/admin/auth/user/",
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": _("Groups"),
                    "icon": "group",
                    "link": "/admin/auth/group/",
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": _("Permissions"),
                    "icon": "lock",
                    "link": "/admin/auth/permission/",
                    "permission": lambda request: request.user.is_superuser,
                },
            ],
        },
        {
            "title": _("Core Management"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Companies"),
                    "icon": "business",
                    "link": "/admin/core/company/",
                    "permission": lambda request: request.user.is_superuser,
                },
            ],
        },
        {
            "title": _("Social Accounts"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Sites"),
                    "icon": "language",
                    "link": reverse_lazy("admin:sites_site_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": _("Social Accounts"),
                    "icon": "account_circle",
                    "link": reverse_lazy("admin:socialaccount_socialaccount_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": _("Social Tokens"),
                    "icon": "vpn_key",
                    "link": reverse_lazy("admin:socialaccount_socialtoken_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": _("Social Apps"),
                    "icon": "apps",
                    "link": reverse_lazy("admin:socialaccount_socialapp_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                },
            ],
        },
        {
            "title": _("Users & Profiles"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Users"),
                    "icon": "people",
                    "link": "/admin/auth/user/",
                },
                {
                    "title": _("Customer Profiles"),
                    "icon": "person",
                    "link": "/admin/cardealing/customerprofile/",
                },
                {
                    "title": _("Dealer Profiles"),
                    "icon": "business",
                    "link": "/admin/cardealing/dealerprofile/",
                },
                {
                    "title": _("Subscription Plans"),
                    "icon": "subscriptions",
                    "link": "/admin/cardealing/subscriptionplan/",
                },
                {
                    "title": _("Commission History"),
                    "icon": "history",
                    "link": "/admin/cardealing/commissionhistory/",
                },
                {
                    "title": _("Customer Verifications"),
                    "icon": "verified",
                    "link": "/admin/cardealing/customerverification/",
                },
                {
                    "title": _("Dealer Verification Documents"),
                    "icon": "verified_user",
                    "link": "/admin/cardealing/dealerverificationdocument/",
                },
            ],
        },
        {
            "title": _("Vehicle Management"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Vehicle Makes"),
                    "icon": "car_rental",
                    "link": "/admin/cardealing/vehiclemake/",
                },
                {
                    "title": _("Vehicle Models"),
                    "icon": "car_repair",
                    "link": "/admin/cardealing/vehiclemodel/",
                },
                {
                    "title": _("Vehicles"),
                    "icon": "directions_car",
                    "link": "/admin/cardealing/vehicle/",
                },
            ],
        },
       {
        "title": _("Service Management"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Service Categories"),
                "icon": "category",
                "link": "/admin/cardealing/servicecategory/",
            },
            {
                "title": _("Services"),
                "icon": "build",
                "link": "/admin/cardealing/service/",
            },
            {
                "title": _("Slot Templates"),
                "icon": "schedule",
                "link": "/admin/cardealing/slottemplate/",
            },
            {
                "title": _("Service Addons"),
                "icon": "add_circle",
                "link": "/admin/cardealing/serviceaddon/",
            },
            {
                "title": _("Technicians"),
                "icon": "engineering",
                "link": "/admin/cardealing/technician/",
            },
            {
                "title": _("Service Slots"),
                "icon": "event",
                "link": "/admin/cardealing/serviceslot/",
            },
            {
                "title": _("Service Availability"),
                "icon": "event_available",
                "link": "/admin/cardealing/serviceavailability/",
            },
        ],
    },
        {
            "title": _("Bookings & Payments"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Bookings"),
                    "icon": "book_online",
                    "link": "/admin/cardealing/booking/",
                },
                {
                    "title": _("Booking Addons"),
                    "icon": "add_shopping_cart",
                    "link": "/admin/cardealing/bookingaddon/",
                },
                {
                    "title": _("Booking Status History"),
                    "icon": "history_toggle_off",
                    "link": "/admin/cardealing/bookingstatushistory/",
                },
                {
                    "title": _("Payments"),
                    "icon": "payment",
                    "link": "/admin/cardealing/payment/",
                },
                {
                    "title": _("Virtual Cards"),
                    "icon": "credit_card",
                    "link": "/admin/cardealing/virtualcard/",
                },
                {
                    "title": _("Dealer Payouts"),
                    "icon": "paid",
                    "link": "/admin/cardealing/dealerpayout/",
                },
                {
                    "title": _("Payout Requests"),
                    "icon": "money",
                    "link": "/admin/cardealing/payoutrequest/",
                },
                {
                    "title": _("Balance Transactions"),
                    "icon": "account_balance",
                    "link": "/admin/cardealing/balancetransaction/",
                },
                {
                    "title": _("Cancellation Policies"),
                    "icon": "policy",
                    "link": "/admin/cardealing/cancellationpolicy/",
                },
            ],
        },
        {
            "title": _("Communication"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Notifications"),
                    "icon": "notifications",
                    "link": "/admin/cardealing/notification/",
                },
                {
                    "title": _("Notification Templates"),
                    "icon": "mail",
                    "link": "/admin/cardealing/notificationtemplate/",
                },
                {
                    "title": _("Reviews"),
                    "icon": "star_rate",
                    "link": "/admin/cardealing/review/",
                },
                {
                    "title": _("Promotions"),
                    "icon": "local_offer",
                    "link": "/admin/cardealing/promotion/",
                },
                {
                    "title": _("Loyalty Transactions"),
                    "icon": "loyalty",
                    "link": "/admin/cardealing/loyaltytransaction/",
                },
            ],
        },
        {
            "title": _("Support System"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Support Tickets"),
                    "icon": "support_agent",
                    "link": "/admin/cardealing/supportticket/",
                },
                {
                    "title": _("Support Messages"),
                    "icon": "message",
                    "link": "/admin/cardealing/supportmessage/",
                },
            ],
        },
        {
            "title": _("Integrations"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("External Integrations"),
                    "icon": "integration_instructions",
                    "link": "/admin/cardealing/externalintegration/",
                },
                {
                    "title": _("Webhook Configurations"),
                    "icon": "webhook",
                    "link": "/admin/cardealing/webhookconfiguration/",
                },
                {
                    "title": _("Webhook Events"),
                    "icon": "event_note",
                    "link": "/admin/cardealing/webhookevent/",
                },
                {
                    "title": _("Sync Logs"),
                    "icon": "sync_alt",
                    "link": "/admin/cardealing/synclog/",
                },
            ],
        },
        {
            "title": _("Analytics"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Booking Analytics"),
                    "icon": "analytics",
                    "link": "/admin/cardealing/bookinganalytics/",
                },
                {
                    "title": _("Dealer Analytics"),
                    "icon": "show_chart",
                    "link": "/admin/cardealing/dealeranalytics/",
                },
            ],
        },
        {
            "title": _("System"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("System Configuration"),
                    "icon": "settings",
                    "link": "/admin/cardealing/systemconfiguration/",
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": _("Admin Actions"),
                    "icon": "history",
                    "link": "/admin/cardealing/adminaction/",
                },
            ],
        },
    ]

UNFOLD = {
    "SITE_TITLE": "Car Service Admin",
    "SITE_HEADER": "Car Service Management",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    
    "COLORS": {
        "primary": {
            "50": "#f0f9ff",
            "100": "#e0f2fe",
            "200": "#bae6fd",
            "300": "#7dd3fc",
            "400": "#38bdf8",
            "500": "#0ea5e9",
            "600": "#0284c7",
            "700": "#0369a1",
            "800": "#075985",
            "900": "#0c4a6e",
        },
        "secondary": {
            "50": "#f8fafc",
            "100": "#f1f5f9",
            "200": "#e2e8f0",
            "300": "#cbd5e1",
            "400": "#94a3b8",
            "500": "#64748b",
            "600": "#475569",
            "700": "#334155",
            "800": "#1e293b",
            "900": "#0f172a",
        },
    },
    
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": get_navigation_for_user,
    },
    
    "THEME": "light",
}

# Environment callback for showing current environment
def environment_callback(request):
    """Show environment indicator"""
    return ["Development", "success"] if settings.DEBUG else ["Production", "danger"]
