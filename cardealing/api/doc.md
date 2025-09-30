# Complete Car Service Booking API Documentation

## Base URL
```
http://localhost:8000/api/v1/
```

---

## 🔐 Authentication Endpoints

### Register New User
```http
POST /auth/register/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123",
  "user_type": "customer",  // or "dealer"
  "first_name": "John",
  "last_name": "Doe"
}
```

### Login (Token)
```http
POST /auth/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password123"
}

Response: {"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
```

### Login (JWT)
```http
POST /auth/jwt/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password123"
}

Response: {
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh JWT Token
```http
POST /auth/jwt/refresh/
Content-Type: application/json

{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}
```

### Get Current User
```http
GET /auth/me/
Authorization: Token YOUR_TOKEN
```

### Update Current User
```http
PATCH /auth/me/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{"first_name": "John", "last_name": "Smith"}
```

### List All Users (Admin Only)
```http
GET /users/
Authorization: Token ADMIN_TOKEN
```

### Get User Detail (Admin Only)
```http
GET /users/1/
Authorization: Token ADMIN_TOKEN
```

### List Groups (Admin Only)
```http
GET /groups/
Authorization: Token ADMIN_TOKEN
```

---

## 👤 Profile Endpoints

### Get Customer Profile
```http
GET /profile/customer/
Authorization: Token YOUR_TOKEN
```

### Update Customer Profile
```http
PATCH /profile/customer/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "phone_number": "+8801712345678",
  "address": "123 Main Street, Dhaka",
  "city": "Dhaka",
  "postal_code": "1000",
  "emergency_contact": "+8801812345678"
}
```

### Get Dealer Profile
```http
GET /profile/dealer/
Authorization: Token DEALER_TOKEN
```

### Update Dealer Profile
```http
PATCH /profile/dealer/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "business_name": "ABC Auto Services",
  "business_phone": "+8801812345678",
  "address": "456 Service Road",
  "city": "Dhaka",
  "service_radius": 15
}
```

### List All Dealers
```http
GET /dealers/
Authorization: Token YOUR_TOKEN
```

### List Subscription Plans
```http
GET /subscription-plans/
Authorization: Token YOUR_TOKEN
```

### Get Subscription Plan Detail
```http
GET /subscription-plans/1/
Authorization: Token YOUR_TOKEN
```

### List Commission History
```http
GET /commission-history/
Authorization: Token DEALER_TOKEN
```

### List Customer Verifications
```http
GET /customer-verifications/
Authorization: Token YOUR_TOKEN
```

### List Dealer Verification Documents
```http
GET /dealer-verification-documents/
Authorization: Token DEALER_TOKEN
```

### Upload Verification Document
```http
POST /dealer-verification-documents/
Authorization: Token DEALER_TOKEN
Content-Type: multipart/form-data

{
  "document_type": "trade_license",
  "document_file": [file upload]
}
```

---

## 🚗 Vehicle Endpoints

### List Vehicle Makes
```http
GET /vehicle-makes/
Authorization: Token YOUR_TOKEN
```

### Create Vehicle Make (Admin Only)
```http
POST /vehicle-makes/
Authorization: Token ADMIN_TOKEN
Content-Type: application/json

{"name": "Toyota", "is_popular": true}
```

### Get Vehicle Make Detail
```http
GET /vehicle-makes/1/
Authorization: Token YOUR_TOKEN
```

### List Vehicle Models
```http
GET /vehicle-models/
Authorization: Token YOUR_TOKEN

// Filter by make
GET /vehicle-models/?make_id=1
```

### Create Vehicle Model (Admin Only)
```http
POST /vehicle-models/
Authorization: Token ADMIN_TOKEN
Content-Type: application/json

{
  "make_id": 1,
  "name": "Camry",
  "year_from": 2015,
  "year_to": 2024
}
```

### List My Vehicles
```http
GET /vehicles/
Authorization: Token YOUR_TOKEN
```

### Add New Vehicle
```http
POST /vehicles/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "make": 1,
  "model": 5,
  "year": 2020,
  "color": "Red",
  "license_plate": "DHAKA-123456",
  "fuel_type": "petrol",
  "transmission": "automatic",
  "engine_cc": 1500,
  "is_primary": true
}
```

### Get Vehicle Detail
```http
GET /vehicles/1/
Authorization: Token YOUR_TOKEN
```

### Update Vehicle
```http
PATCH /vehicles/1/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{"current_mileage": 15000, "color": "Blue"}
```

### Delete Vehicle
```http
DELETE /vehicles/1/
Authorization: Token YOUR_TOKEN
```

---

## 🔧 Service Endpoints

### List Service Categories
```http
GET /service-categories/
Authorization: Token YOUR_TOKEN
```

### Create Service Category (Admin Only)
```http
POST /service-categories/
Authorization: Token ADMIN_TOKEN
Content-Type: application/json

{
  "name": "Engine Service",
  "description": "All engine related services",
  "estimated_duration": 120
}
```

### Get Service Category Detail
```http
GET /service-categories/1/
Authorization: Token YOUR_TOKEN
```

### List All Services
```http
GET /services/
Authorization: Token YOUR_TOKEN

// With filters
GET /services/?category=1&dealer=5
```

### Get Service Detail
```http
GET /services/1/
Authorization: Token YOUR_TOKEN
```

### List My Services (Dealer)
```http
GET /dealer/services/
Authorization: Token DEALER_TOKEN
```

### Create Service (Dealer)
```http
POST /dealer/services/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "category_id": 1,
  "name": "Full Car Service",
  "description": "Complete car servicing with oil change and inspection",
  "short_description": "Full service package",
  "base_price": "3500.00",
  "estimated_duration": 120,
  "service_location": "workshop",
  "supported_fuel_types": ["petrol", "diesel"]
}
```

### Get My Service Detail (Dealer)
```http
GET /dealer/services/1/
Authorization: Token DEALER_TOKEN
```

### Update Service (Dealer)
```http
PATCH /dealer/services/1/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "base_price": "4000.00",
  "is_featured": true,
  "is_active": true
}
```

### Delete Service (Dealer)
```http
DELETE /dealer/services/1/
Authorization: Token DEALER_TOKEN
```

### List Service Addons
```http
GET /service-addons/
Authorization: Token YOUR_TOKEN

// Filter by service
GET /service-addons/?service_id=1
```

### Create Service Addon
```http
POST /service-addons/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "service_id": 1,
  "name": "Air Filter Replacement",
  "description": "Replace air filter",
  "price": "500.00"
}
```

### List My Technicians (Dealer)
```http
GET /technicians/
Authorization: Token DEALER_TOKEN
```

### Add Technician (Dealer)
```http
POST /technicians/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "name": "Ahmed Khan",
  "phone_number": "+8801712345678",
  "expertise": ["engine_service", "brake_service"]
}
```

### Get Technician Detail (Dealer)
```http
GET /technicians/1/
Authorization: Token DEALER_TOKEN
```

### Update Technician (Dealer)
```http
PATCH /technicians/1/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{"is_available": false}
```

### Delete Technician (Dealer)
```http
DELETE /technicians/1/
Authorization: Token DEALER_TOKEN
```

---

## 📅 Service Slot Endpoints

### List Available Slots
```http
GET /service-slots/
Authorization: Token YOUR_TOKEN

// Filters
GET /service-slots/?service_id=1&date=2025-10-15
```

### List My Slots (Dealer)
```http
GET /dealer/slots/
Authorization: Token DEALER_TOKEN
```

### Create Slot (Dealer)
```http
POST /dealer/slots/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "service_id": 1,
  "date": "2025-10-15",
  "start_time": "09:00",
  "end_time": "11:00",
  "total_capacity": 2,
  "available_capacity": 2
}
```

### Get Slot Detail (Dealer)
```http
GET /dealer/slots/1/
Authorization: Token DEALER_TOKEN
```

### Update Slot (Dealer)
```http
PATCH /dealer/slots/1/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{"is_blocked": true, "block_reason": "Holiday"}
```

### Delete Slot (Dealer)
```http
DELETE /dealer/slots/1/
Authorization: Token DEALER_TOKEN
```

---

## 📝 Booking Endpoints

### List Cancellation Policies
```http
GET /cancellation-policies/
Authorization: Token YOUR_TOKEN
```

### List Active Promotions
```http
GET /promotions/
Authorization: Token YOUR_TOKEN
```

### Validate Promotion Code
```http
POST /promotions/validate/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{"code": "SUMMER2025"}
```

### List My Bookings
```http
GET /bookings/
Authorization: Token YOUR_TOKEN
```

### Create Booking
```http
POST /bookings/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "service_slot_id": 10,
  "vehicle_id": 2,
  "service_location": "workshop",
  "service_amount": "3500.00",
  "tax_amount": "350.00",
  "total_amount": "3850.00",
  "special_instructions": "Please check brakes"
}
```

### Get Booking Detail
```http
GET /bookings/1/
Authorization: Token YOUR_TOKEN
```

### Cancel Booking
```http
POST /bookings/1/cancel/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{"reason": "Schedule conflict"}
```

### Confirm Booking (Dealer)
```http
POST /bookings/1/confirm/
Authorization: Token DEALER_TOKEN
```

### List Booking Addons
```http
GET /booking-addons/?booking_id=1
Authorization: Token YOUR_TOKEN
```

### List Booking Status History
```http
GET /booking-status-history/?booking_id=1
Authorization: Token YOUR_TOKEN
```

---

## 💳 Payment & Payout Endpoints

### List My Virtual Cards (Dealer)
```http
GET /virtual-cards/
Authorization: Token DEALER_TOKEN
```

### List My Payments
```http
GET /payments/
Authorization: Token YOUR_TOKEN
```

### Get Payment Detail
```http
GET /payments/1/
Authorization: Token YOUR_TOKEN
```

### List My Payouts (Dealer)
```http
GET /dealer/payouts/
Authorization: Token DEALER_TOKEN
```

### Request Payout (Dealer)
```http
POST /dealer/payouts/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{
  "amount": "50000.00",
  "processing_fee": "1000.00",
  "bank_details": {
    "account_number": "1234567890",
    "bank_name": "ABC Bank",
    "account_holder": "John's Auto Service"
  }
}
```

### Get Payout Detail (Dealer)
```http
GET /dealer/payouts/1/
Authorization: Token DEALER_TOKEN
```

### List Balance Transactions (Dealer)
```http
GET /balance-transactions/
Authorization: Token DEALER_TOKEN
```

---

## ⭐ Loyalty & Review Endpoints

### List My Loyalty Transactions
```http
GET /loyalty-transactions/
Authorization: Token YOUR_TOKEN
```

### List Reviews
```http
GET /reviews/
Authorization: Token YOUR_TOKEN

// Reviews for specific dealer
GET /reviews/?dealer_id=5
```

### Create Review
```http
POST /reviews/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "booking_id": 10,
  "overall_rating": 5,
  "service_quality": 5,
  "punctuality": 4,
  "value_for_money": 5,
  "title": "Excellent Service",
  "comment": "Very satisfied with the quality"
}
```

### Get Review Detail
```http
GET /reviews/1/
Authorization: Token YOUR_TOKEN
```

### Respond to Review (Dealer)
```http
POST /reviews/1/respond/
Authorization: Token DEALER_TOKEN
Content-Type: application/json

{"response": "Thank you for your feedback!"}
```

---

## 🔔 Notification Endpoints

### List My Notifications
```http
GET /notifications/
Authorization: Token YOUR_TOKEN
```

### Mark Notification as Read
```http
POST /notifications/1/read/
Authorization: Token YOUR_TOKEN
```

### List Notification Templates (Admin)
```http
GET /notification-templates/
Authorization: Token ADMIN_TOKEN
```

---

## 🆘 Support Endpoints

### List My Support Tickets
```http
GET /support/tickets/
Authorization: Token YOUR_TOKEN
```

### Create Support Ticket
```http
POST /support/tickets/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "subject": "Payment Issue",
  "description": "I was charged twice",
  "category": "payment_problem",
  "priority": "high"
}
```

### Get Ticket Detail
```http
GET /support/tickets/1/
Authorization: Token YOUR_TOKEN
```

### Update Ticket
```http
PATCH /support/tickets/1/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{"status": "resolved"}
```

### List Messages for Ticket
```http
GET /support/messages/?ticket_id=1
Authorization: Token YOUR_TOKEN
```

### Send Message
```http
POST /support/messages/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "ticket_id": 1,
  "message": "Here are the transaction details..."
}
```

---

## 🔌 Integration Endpoints

### List My Integrations (Dealer)
```http
GET /external-integrations/
Authorization: Token DEALER_TOKEN
```

### List Webhook Events (Dealer)
```http
GET /webhook-events/
Authorization: Token DEALER_TOKEN
```

### List Sync Logs (Dealer)
```http
GET /sync-logs/
Authorization: Token DEALER_TOKEN
```

---

## 📊 Analytics Endpoints

### List Booking Analytics (Admin)
```http
GET /booking-analytics/
Authorization: Token ADMIN_TOKEN
```

### List My Dealer Analytics
```http
GET /dealer-analytics/
Authorization: Token DEALER_TOKEN
```

---

## ⚙️ System Endpoints

### List System Configurations (Admin)
```http
GET /system-configuration/
Authorization: Token ADMIN_TOKEN
```

### List Admin Actions (Admin)
```http
GET /admin-actions/
Authorization: Token ADMIN_TOKEN
```

---

## Response Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Deleted successfully
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - No permission
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Error Format

```json
{
  "error": "Error description"
}
```

Or validation errors:
```json
{
  "field_name": ["Error message"]
}
```

---

## Notes

1. All endpoints require authentication except `/auth/register/` and `/auth/login/`
2. Use `Authorization: Token YOUR_TOKEN` header
3. All dates: `YYYY-MM-DD` format
4. All times: `HH:MM` format (24-hour)
5. Currency: BDT (Bangladeshi Taka)
6. Decimal fields: 2 decimal places