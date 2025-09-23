from django.contrib import admin
from .models import Flight, Airport, Airplane, Ticket, Country, Airline

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
    list_display = ("id", "model", "capacity")
    search_fields = ("model",)
    list_filter = ("capacity",)

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", 'airport')
    search_fields = ("name",)
    list_filter = ("airport",)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "departure_airport",
        "arrival_airport",
        "airplane",
        "departure_time",
        "arrival_time",
    )
    search_fields = ("departure_airport__name", "arrival_airport__name")
    list_filter = ("airplane", "departure_time", "arrival_time")

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "flight", "ticket_type", "return_flight", "status", "price", "created_at")
    search_fields = ("user__email", "flight__flight_number", "return_flight__flight_number")
    list_filter = ("ticket_type", "status", "created_at")
    readonly_fields = ("created_at",)
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'ticket_type', 'status', 'price', 'created_at')
        }),
        ('Outbound Flight', {
            'fields': ('flight', 'seat_number')
        }),
        ('Return Flight', {
            'fields': ('return_flight',),
            'description': 'Only required for round trip tickets'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'flight', 'return_flight')
