from django.contrib import admin
from .models import Airport, Airplane, Country, Airline

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
