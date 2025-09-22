# flights/admin.py
from django.contrib import admin
from django import forms
from django.db import transaction
from django.db.models import Count, Q
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from users.models import User


# ---------------------------
# Admin site branding (опціонально)
# ---------------------------
admin.site.site_header = "Flights Admin"
admin.site.site_title = "Flights Admin Portal"
admin.site.index_title = "Керування рейсами та квитками"


# ---------------------------
# Country
# ---------------------------
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


# ---------------------------
# Airport
# ---------------------------
@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "slug")
    list_filter = ("country",)
    search_fields = ("name", "city", "country__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("country",)
    ordering = ("country__name", "city", "name")


# ---------------------------
# Airline & Airplane inlines
# ---------------------------
class AirplaneInline(admin.TabularInline):
    model = Airplane
    fields = ("model", "capacity", "slug")
    readonly_fields = ("slug",)
    extra = 0
    show_change_link = True


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("name", "airport", "slug")
    search_fields = ("name", "airport__name", "airport__city")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("airport",)
    inlines = (AirplaneInline,)
    ordering = ("name",)


# ---------------------------
# Airplane admin
# ---------------------------
@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ("model", "airline", "capacity", "slug")
    list_filter = ("airline",)
    search_fields = ("model", "airline__name")
    prepopulated_fields = {"slug": ("model",)}
    autocomplete_fields = ("airline",)
    ordering = ("airline__name", "model")


# ---------------------------
# Forms for Flight and Ticket admin (додаємо валідацію)
# ---------------------------
class FlightAdminForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        dep = cleaned.get("departure_time")
        arr = cleaned.get("arrival_time")
        if dep and arr and arr <= dep:
            raise ValidationError(_("Arrival time must be later than departure time."))

        airplane = cleaned.get("airplane") or getattr(self.instance, "airplane", None)
        if airplane and self.instance.pk:
            # Якщо змінюємо airplane, перевірити що поточні заброньовані місця вміщуються
            occupied = self.instance.tickets.exclude(status=Ticket.TicketStatus.FAILED).count()
            if airplane.capacity < occupied:
                raise ValidationError(
                    _(
                        "Selected airplane capacity (%(cap)s) is less than already booked seats (%(occ)s)."
                    ) % {"cap": airplane.capacity, "occ": occupied}
                )
        return cleaned


class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        flight = cleaned.get("flight") or getattr(self.instance, "flight", None)
        seat = cleaned.get("seat_number") or getattr(self.instance, "seat_number", None)
        status = cleaned.get("status") or getattr(self.instance, "status", None)

        if not flight:
            raise ValidationError(_("Flight is required."))

        # Унікальність місця на рівні форми (додатково до БД/моделі)
        qs = Ticket.objects.filter(flight=flight, seat_number__iexact=seat)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(_("This seat is already taken for the flight."))

        # Перевірка capacity (рахуємо тільки не-Failed квитки)
        occupied = flight.tickets.exclude(status=Ticket.TicketStatus.FAILED)
        if self.instance.pk:
            occupied = occupied.exclude(pk=self.instance.pk)
        occupied_count = occupied.count()
        # якщо статус не 'failed' — квитка буде займати місце
        takes_seat = (status != Ticket.TicketStatus.FAILED)
        if takes_seat and (occupied_count + 1) > flight.airplane.capacity:
            raise ValidationError(
                _(
                    "Cannot save ticket: airplane capacity %(cap)s exceeded (occupied %(occ)s)."
                ) % {"cap": flight.airplane.capacity, "occ": occupied_count}
            )

        # Заборона бронювання на рейс, що вже вилетів (якщо потрібно)
        from django.utils import timezone
        if flight.departure_time and flight.departure_time <= timezone.now():
            raise ValidationError(_("Cannot create/edit ticket for a flight that already departed."))

        return cleaned


# ---------------------------
# Inline: Tickets in Flight admin (корисно для перегляду)
# ---------------------------
class TicketInline(admin.TabularInline):
    model = Ticket
    fields = ("user", "seat_number", "status", "price", "created_at")
    readonly_fields = ("created_at",)
    extra = 0
    show_change_link = True
    autocomplete_fields = ("user",)


# ---------------------------
# Flight admin
# ---------------------------
@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    form = FlightAdminForm
    list_display = (
        "flight_number",
        "departure_airport_city",
        "arrival_airport_city",
        "departure_time",
        "arrival_time",
        "status",
        "airplane_capacity",
        "occupied_seats",
        "available_seats_display",
    )
    list_filter = ("status", "departure_airport", "arrival_airport", "airplane")
    search_fields = ("flight_number", "departure_airport__city", "arrival_airport__city", "airplane__model")
    ordering = ("-departure_time",)
    inlines = (TicketInline,)
    autocomplete_fields = ("airplane", "departure_airport", "arrival_airport")
    readonly_fields = ("occupied_seats", "available_seats_display")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # анотуємо загальну кількість квитків і кількість failed, щоб порахувати "occupied" ефективно
        qs = qs.annotate(
            total_tickets=Count("tickets", distinct=True),
            failed_tickets=Count("tickets", filter=Q(tickets__status=Ticket.TicketStatus.FAILED), distinct=True),
        ).select_related("airplane", "departure_airport", "arrival_airport")
        return qs

    def airplane_capacity(self, obj):
        return obj.airplane.capacity if obj.airplane else "-"
    airplane_capacity.short_description = _("Capacity")

    def occupied_seats(self, obj):
        # occupied = total - failed
        total = getattr(obj, "total_tickets", None)
        failed = getattr(obj, "failed_tickets", None)
        if total is not None and failed is not None:
            return max(total - failed, 0)
        # fallback — DB call
        return obj.tickets.exclude(status=Ticket.TicketStatus.FAILED).count()
    occupied_seats.short_description = _("Occupied")

    def available_seats_display(self, obj):
        cap = obj.airplane.capacity if obj.airplane else 0
        occ = self.occupied_seats(obj)
        available = max(cap - occ, 0)
        return f"{available} / {cap}"
    available_seats_display.short_description = _("Available / Capacity")


# ---------------------------
# Ticket admin
# ---------------------------
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = ("id", "user_email", "flight_number", "seat_number", "price", "status", "created_at")
    list_filter = ("status", "flight__departure_time")
    search_fields = ("user__email", "flight__flight_number", "seat_number")
    ordering = ("-created_at",)
    autocomplete_fields = ("flight", "user")
    actions = ("mark_tickets_paid", "mark_tickets_failed", "export_selected_as_csv",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "flight", "flight__airplane")

    def user_email(self, obj):
        return obj.user.email if obj.user else "-"
    user_email.short_description = _("User")

    def flight_number(self, obj):
        return obj.flight.flight_number if obj.flight else "-"
    flight_number.short_description = _("Flight")

    @admin.action(description=_("Mark selected tickets as PAID"))
    def mark_tickets_paid(self, request, queryset):
        updated = queryset.update(status=Ticket.TicketStatus.PAID)
        self.message_user(request, _("%d ticket(s) marked as PAID.") % updated)

    @admin.action(description=_("Mark selected tickets as FAILED"))
    def mark_tickets_failed(self, request, queryset):
        # Використовуємо транзакцію, щоб уникнути напів-змін
        with transaction.atomic():
            updated = queryset.update(status=Ticket.TicketStatus.FAILED)
        self.message_user(request, _("%d ticket(s) marked as FAILED.") % updated)

    @admin.action(description=_("Export selected tickets as CSV"))
    def export_selected_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        meta = self.model._meta
        field_names = ["id", "user_email", "flight_number", "seat_number", "price", "status", "created_at"]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="tickets_export.csv"'
        writer = csv.writer(response)
        writer.writerow(field_names)

        for obj in queryset.select_related("user", "flight"):
            writer.writerow([
                obj.pk,
                obj.user.email if obj.user else "",
                obj.flight.flight_number if obj.flight else "",
                obj.seat_number,
                str(obj.price),
                obj.status,
                obj.created_at.isoformat(),
            ])
        return response
