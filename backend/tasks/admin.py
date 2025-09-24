from django.contrib import admin
from .models import (Flight, Airport, Airplane, 
                     Ticket, Country, Airline, Seat, Order)

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
    list_display = ("id", "model",  "get_total_seats_display", "economy_seats", "business_seats", "first_class_seats", "airline")
    search_fields = ("model", "airline__name")
    list_filter = ("airline", )
    readonly_fields = ("get_total_seats_display", )
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'airline')
        }),
        ('Seat Configuration', {
            'fields': (
                ('economy_seats', 'rows_economy', 'seats_per_row_economy'),
                ('business_seats', 'rows_business', 'seats_per_row_business'),
                ('first_class_seats', 'rows_first_class', 'seats_per_row_first_class'),
            )
        }),
    )
    
    def get_total_seats_display(self, obj):
        return obj.get_total_seats()
    get_total_seats_display.short_descriptions = "Total Seats"

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

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("id", "seat_number", "airplane", "seat_class", "row_number", "seat_letter", "status", "is_window_seat", "is_aisle_seat")
    search_fields = ("seat_number", "airplane__model")
    list_filter = ("airplane", "seat_class", "status", "is_window_seat", "is_aisle_seat", "is_emergency_exit", "extra_legroom")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ('Basic Information', {
            'fields': ('airplane', 'seat_number', 'seat_class', 'status')
        }),
        ('Seat Position', {
            'fields': ('row_number', 'seat_letter')
        }),
        ('Seat Features', {
            'fields': ('is_window_seat', 'is_aisle_seat', 'is_emergency_exit', 'extra_legroom')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('airplane', 'airplane__airline')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "flight", "seat", "ticket_type", "return_flight", "status", "price", "created_at")
    search_fields = ("user__email", "flight__flight_number", "return_flight__flight_number", "seat__seat_number")
    list_filter = ("ticket_type", "status", "created_at", "seat__seat_class")
    readonly_fields = ("created_at",)
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'ticket_type', 'status', 'price', 'created_at')
        }),
        ('Outbound Flight', {
            'fields': ('flight', 'seat', 'seat_number')
        }),
        ('Return Flight', {
            'fields': ('return_flight',),
            'description': 'Only required for round trip tickets'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'flight', 'return_flight', 'seat')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "flight",
        "seat",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "flight__code", "seat__seat_number")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("status",)

    fieldsets = (
        ("Main information", {
            "fields": ("user", "flight", "seat", "status")
        }),
        ("System fields", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )