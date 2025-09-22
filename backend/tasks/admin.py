from django.contrib import admin
from .models import Flight, Airport, Airplane, Ticket, Country


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
    list_display = ("id", "flight", "status")
    search_fields = ("flight__id",)
    list_filter = ("status",)
