from django.contrib import admin
from .models import Bus, Booking

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'source', 'destination', 'departure_time', 'arrival_time', 'total_seats', 'available_seats', 'price')
    search_fields = ('name', 'source', 'destination')
    list_filter = ('source', 'destination', 'departure_time')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'bus', 'seats_booked', 'amount_paid', 'booked_on', 'payment_status')
    search_fields = ('user__username', 'bus__name')
    list_filter = ('payment_status', 'booked_on')
