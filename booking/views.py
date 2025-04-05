import razorpay
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from django.urls import reverse
from .models import Bus, Booking
from django.conf import settings
from decimal import Decimal

# Razorpay client initialization
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

def home(request):
    return render(request, 'booking/index.html')


# User Registration View
def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Try a different one.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered. Try logging in.")
            else:
                User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, "Registration successful! Please log in.")
                return redirect("booking:login")  # Redirect to login page

    else:
        form = RegisterForm()

    return render(request, "booking/register.html", {"form": form})

# User Login View
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("booking:dashboard")  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, "booking/login.html")

# Logout View
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("booking:login")  # Redirect to login page

# Dashboard Page (Protected)
@login_required(login_url="booking:login")  # Redirects to login if not logged in
def user_dashboard(request):
    return render(request, "booking/dashboard.html")


# views.py
from django.contrib.auth.decorators import login_required
from .models import Booking

# views.py
@login_required
def booking_history(request):
    # Fetch the logged-in user's bookings
    bookings = Booking.objects.filter(user=request.user).order_by('-booked_on')
    return render(request, 'booking/booking_history.html', {'bookings': bookings})

# views.py
from django.shortcuts import render, redirect

# def booking_page(request):
#     return render(request, 'booking/booking_page.html')

def booking_page(request):
    from django.db.models import Count
    buses = Bus.objects.all()
    unique_sources = Bus.objects.values('source', 'departure_time').distinct()
    unique_destination = Bus.objects.values('destination', 'arrival_time').distinct()
    return render(request, 'booking/booking_page.html', {'buses': buses, 'sources': unique_sources, 'destinations':unique_destination})


def confirm_booking(request):
    if request.method == 'POST':
        # Store form data in session
        request.session['booking_data'] = {
            'from': request.POST.get('from'),
            'to': request.POST.get('to'),
            
            'date': request.POST.get('date'),
            'passengers': request.POST.get('passengers'),
            'seattype': request.POST.get('seattype'),
            'total_amount': request.POST.get('total_amount').replace('₹', ''),
        }
        # Render the confirmation page directly
        return render(request, 'booking/confirm_booking.html', {
            'booking_data': request.session['booking_data'],
        })
    return redirect('booking_page')

# views.py
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect


import time

def payment(request):
    if request.method == 'POST':
        # Retrieve booking data from session
        booking_data = request.session.get('booking_data', {})

        # Ensure amount is dynamically fetched from booking_data
        amount = int(float(booking_data.get('total_amount', 0))) * 100  # Convert ₹ to paise
        if amount <= 0:
            return redirect('confirm_booking')  # Prevent processing invalid amounts

        currency = 'INR'
        receipt = f'order_rcptid_{request.user.id}_{int(time.time())}'  # Unique receipt ID

        payment_order = razorpay_client.order.create({
            'amount': amount,
            'currency': currency,
            'receipt': receipt,
            'payment_capture': 1  # Auto-capture payment
        })

        # Store the order ID in session for verification later
        request.session['razorpay_order_id'] = payment_order['id']

        # Render the payment page with Razorpay details
        return render(request, 'booking/payment.html', {
            'booking_data': booking_data,
            'razorpay_order_id': payment_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': amount,
        })
    
    return redirect('confirm_booking')  # Redirect back if not POST


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Booking, Bus

@login_required
def payment_success(request):
    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    razorpay_order_id = request.session.get('razorpay_order_id')
    booking_data = request.session.get('booking_data', {})

    print(f"Razorpay Payment ID: {razorpay_payment_id}")
    print(f"Razorpay Order ID: {razorpay_order_id}")
    print(f"Booking Data: {booking_data}")

    if razorpay_payment_id and razorpay_order_id and booking_data:
        try:
            # Fetch payment details from Razorpay
            payment = razorpay_client.payment.fetch(razorpay_payment_id)
            print(f"Payment Details: {payment}")

            # Verify that the payment belongs to the correct order
            if payment['order_id'] == razorpay_order_id:
                # Save booking details to the database
                bus = Bus.objects.get(id=1)  # Replace with logic to fetch the correct bus
                Booking.objects.create(
                    user=request.user,
                    bus=bus,
                    seats_booked=int(booking_data['passengers']),
                    amount_paid=float(payment['amount']) / 100,  # Convert paise to rupees
                    payment_status=True,
                )

                # Clear session data
                request.session.pop('booking_data', None)
                request.session.pop('razorpay_order_id', None)

                print("Booking History URL:", reverse('booking:booking_history'))
                return redirect('booking:booking_history')  # Use app namespace
            else:
                print("Order ID mismatch")
        except Exception as e:
            print(f"Payment verification or database save failed: {e}")
    else:
        print("Missing payment or booking data")

    return render(request, 'booking/payment_failed.html')


# def payment_success(request):
#     razorpay_payment_id = request.GET.get('razorpay_payment_id')
#     razorpay_order_id = request.session.get('razorpay_order_id')

#     print(f"Razorpay Payment ID: {razorpay_payment_id}")
#     print(f"Razorpay Order ID: {razorpay_order_id}")

#     if razorpay_payment_id and razorpay_order_id:
#         try:
#             payment = razorpay_client.payment.fetch(razorpay_payment_id)
#             print(f"Payment Details: {payment}")

#             if payment['order_id'] == razorpay_order_id:
#                 return render(request, 'booking/payment_success.html', {
#                     'payment_id': razorpay_payment_id,
#                 })
#         except Exception as e:
#             print(f"Payment verification failed: {e}")

#     return render(request, 'booking/payment_failed.html')

# Reviews & Ratings Page
@login_required(login_url="booking:login")
def reviews(request):
    return render(request, "booking/reviews.html")

# Cancellation & Refund Page
@login_required(login_url="booking:login")
def cancellation_refund(request):
    return render(request, "booking/cancellation_refund.html")


def privacy_policy(request):
    return render(request, "booking/privacy_policy.html")

def terms_of_service(request):
    return render(request, "booking/terms_of_service.html")

def contact(request):
    return render(request, "booking/contact.html")

def about(request):
    return render(request, "booking/about.html")

def faq(request):
    return render(request, "booking/faq.html")



def help_center(request):
    return render(request, "booking/help.html")