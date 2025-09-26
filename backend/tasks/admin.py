from django.contrib import admin
from .models import Flight, Airport, Airplane, Order, Ticket, Country, Airline


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    list_filter = ("name",)

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "country")
    search_fields = ("name", "city")
    list_filter = ("country",)

@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ("id", "model", "capacity", "economy_seats", "business_seats", "first_class_seats", "airline")
    search_fields = ("model", "airline__name")
    list_filter = ("capacity", "airline")
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'airline', 'capacity')
        }),
        ('Seat Configuration', {
            'fields': (
                ('economy_seats', 'business_seats', 'first_class_seats'),
            )
        }),
    )

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", 'airport')
    search_fields = ("name",)
    list_filter = ("airport",)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ("id", "flight_number", "departure_airport", "arrival_airport", "airplane", "departure_time", "arrival_time", "status")
    search_fields = ("flight_number", "departure_airport__name", "arrival_airport__name")
    list_filter = ("airplane", "departure_time", "arrival_time", "status")
    fieldsets = (
        ('Basic Information', {
            'fields': ('flight_number', 'airplane', 'status')
        }),
        ('Route', {
            'fields': ('departure_airport', 'arrival_airport')
        }),
        ('Schedule', {
            'fields': ('departure_time', 'arrival_time')
        }),
        ('Seat Availability', {
            'fields': ('economy_seats', 'business_seats', 'first_class_seats')
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "flight", "return_flight", "ticket_type", "status", "total_price", "created_at")
    search_fields = ("user__email", "flight__flight_number", "return_flight__flight_number")
    list_filter = ("ticket_type", "status", "created_at")
    readonly_fields = ("created_at",)
    actions = ['confirm_orders', 'cancel_orders']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'ticket_type', 'status', 'total_price', 'created_at')
        }),
        ('Flights', {
            'fields': ('flight', 'return_flight')
        }),
    )

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "seat_number", "seat_class", "direction", "price")
    search_fields = ("seat_number", "order__user__email", "order__flight__flight_number")
    list_filter = ("seat_class", "direction")
    fieldsets = (
        ('Basic Information', {
            'fields': ('order', 'seat_number', 'seat_class', 'direction', 'price')
        }),
    )
