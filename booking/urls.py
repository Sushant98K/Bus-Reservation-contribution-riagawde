from django.urls import path
from . import views

app_name = 'booking'  # Namespacing the app

urlpatterns = [
    # User Authentication URLs
       path('', views.home, name='home'), 
    path("register/", views.user_register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    
    # Dashboard & Booking URLs
    path("dashboard/", views.user_dashboard, name="dashboard"),
    path('booking/history/', views.booking_history, name='booking_history'),
    path('book/', views.booking_page, name='booking'),
    path('confirm-booking/', views.confirm_booking, name='confirm_booking'),
   
    path('payment/', views.payment, name='payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path("contact/", views.contact, name="contact"),
    
    # Reviews & Cancellation
    path("reviews/", views.reviews, name="reviews"),
    path("cancellation-refund/", views.cancellation_refund, name="cancellation_refund"),
    
    # Static Pages
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service/", views.terms_of_service, name="terms_of_service"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("help-center/", views.help_center, name="help_center"),
]
