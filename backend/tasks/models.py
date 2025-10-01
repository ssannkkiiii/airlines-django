from django.db import models, transaction
from django.utils.text import slugify
from users.models import User
from django.core.exceptions import ValidationError


class Country(models.Model):
    slug = models.SlugField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name='Country name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'country'
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'


class Airport(models.Model):
    slug = models.SlugField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name='Airport name')
    city = models.CharField(max_length=255, verbose_name="City name")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='airports')

    def __str__(self):
        return f"Airport {self.name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'airport'
        verbose_name = 'Airport'
        verbose_name_plural = 'Airports'


class Airline(models.Model):
    slug = models.SlugField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=100, verbose_name="Airline name")
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="airlines")

    def __str__(self):
        return f"Airline {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'airline'
        verbose_name = 'Airline'
        verbose_name_plural = 'Airlines'


class Airplane(models.Model):
    slug = models.SlugField(unique=True, null=True, blank=True)
    model = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name="airplanes")
    economy_seats = models.PositiveIntegerField(default=0, help_text="Number of economy class seats")
    business_seats = models.PositiveIntegerField(default=0, help_text="Number of business class seats")
    first_class_seats = models.PositiveIntegerField(default=0, help_text="Number of first class seats")

    def __str__(self):
        return f"Airplane {self.model} of {self.airline.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.model)
        self.capacity = self.economy_seats + self.business_seats + self.first_class_seats
        super().save(*args, **kwargs)

    def get_total_seats(self):
        return self.economy_seats + self.business_seats + self.first_class_seats

    def get_seat_configuration(self):
        return {
            'economy': {'total_seats': self.economy_seats},
            'business': {'total_seats': self.business_seats},
            'first_class': {'total_seats': self.first_class_seats}
        }

    class Meta:
        db_table = 'airplane'
        verbose_name = 'Airplane'
        verbose_name_plural = 'Airplanes'


class Flight(models.Model):
    class FlightStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        BOARDING = 'boarding', 'Boarding'
        DEPARTED = 'departed', 'Departed'
        DELAYED = 'delayed', 'Delayed'
        CANCELLED = 'cancelled', 'Cancelled'

    class SeatClass(models.TextChoices):
        ECONOMY = 'economy', 'Economy'
        BUSINESS = 'business', 'Business'
        FIRST_CLASS = 'first_class', 'First Class'

    flight_number = models.CharField(max_length=10, unique=True)
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    departure_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="departures")
    arrival_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="arrivals")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=FlightStatus.choices, default=FlightStatus.SCHEDULED)
    economy_seats = models.PositiveIntegerField(default=0)
    business_seats = models.PositiveIntegerField(default=0)
    first_class_seats = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.city} -> {self.arrival_airport.city}"

    def save(self, *args, **kwargs):
        if not self.pk and self.airplane_id:
            airplane = self.airplane
            self.economy_seats = airplane.economy_seats
            self.business_seats = airplane.business_seats
            self.first_class_seats = airplane.first_class_seats
        super().save(*args, **kwargs)

    def get_available_seats(self, seat_class):
        if seat_class == self.SeatClass.ECONOMY:
            return self.economy_seats
        elif seat_class == self.SeatClass.BUSINESS:
            return self.business_seats
        elif seat_class == self.SeatClass.FIRST_CLASS:
            return self.first_class_seats
        return 0

    def book_seat(self, seat_class):
        if seat_class == self.SeatClass.ECONOMY and self.economy_seats > 0:
            self.economy_seats -= 1
            self.save(update_fields=['economy_seats'])
            return True
        elif seat_class == self.SeatClass.BUSINESS and self.business_seats > 0:
            self.business_seats -= 1
            self.save(update_fields=['business_seats'])
            return True
        elif seat_class == self.SeatClass.FIRST_CLASS and self.first_class_seats > 0:
            self.first_class_seats -= 1
            self.save(update_fields=['first_class_seats'])
            return True
        return False

    class Meta:
        db_table = 'flight'
        verbose_name = 'Flight'
        verbose_name_plural = 'Flights'


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    class TicketType(models.TextChoices):
        ONE_WAY = 'one_way', 'One Way'
        ROUND_TRIP = 'round_trip', 'Round Trip'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="orders")
    return_flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="return_orders",
        null=True,
        blank=True
    )
    ticket_type = models.CharField(max_length=20, choices=TicketType.choices, default=TicketType.ONE_WAY)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.BOOKED)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tickets_data = models.JSONField(null=True, blank=True, help_text="Stored ticket data for later creation")

    def clean(self):
        if self.ticket_type == self.TicketType.ROUND_TRIP and not self.return_flight:
            raise ValidationError('Return flight is required for round trip tickets.')

        if self.ticket_type == self.TicketType.ONE_WAY and self.return_flight:
            raise ValidationError('Return flight should not be specified for one way tickets.')

        if self.return_flight and self.return_flight == self.flight:
            raise ValidationError('Return flight must be different from outbound flight.')

        if self.return_flight and self.return_flight.departure_time <= self.flight.arrival_time:
            raise ValidationError('Return flight departure must be after outbound flight arrival.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_one_way(self):
        return self.ticket_type == self.TicketType.ONE_WAY

    @property
    def is_round_trip(self):
        return self.ticket_type == self.TicketType.ROUND_TRIP

    def buy(self):
        if self.status != self.OrderStatus.BOOKED:
            raise ValueError("Only booked orders can be bought")

        if not self.tickets_data:
            raise ValueError("No ticket data found for this order")

        with transaction.atomic():
            for ticket_data in self.tickets_data:
                direction = ticket_data.get('direction', 'outbound')
                target_flight = self.return_flight if direction == 'return' else self.flight
                
                if not target_flight:
                    raise ValueError(f"No flight available for {direction} direction.")
                
                available_seats = target_flight.get_available_seats(ticket_data['seat_class'])
                if available_seats <= 0:
                    flight_name = "return flight" if direction == 'return' else "outbound flight"
                    raise ValueError(f"{flight_name}: No {ticket_data['seat_class']} seats available.")
                
                if not target_flight.book_seat(ticket_data['seat_class']):
                    flight_name = "return flight" if direction == 'return' else "outbound flight"
                    raise ValueError(f"{flight_name}: Failed to book {ticket_data['seat_class']} seat.")
                
                Ticket.objects.create(
                    order=self,
                    seat_number=ticket_data['seat_number'],
                    seat_class=ticket_data['seat_class'],
                    direction=Ticket.TicketDirection.OUTBOUND if direction == 'outbound' else Ticket.TicketDirection.RETURN,
                    price=ticket_data['price']
                )
            
            self.tickets_data = None
            self.status = self.OrderStatus.CONFIRMED
            self.save()
        
        return True

    def cancel(self):
        if self.status == self.OrderStatus.CANCELLED:
            raise ValueError("Order is already cancelled")

        with transaction.atomic():
            if self.status == self.OrderStatus.CONFIRMED:
                for ticket in self.tickets.all():
                    if ticket.direction == ticket.TicketDirection.OUTBOUND:
                        if ticket.seat_class == Flight.SeatClass.ECONOMY:
                            self.flight.economy_seats += 1
                        elif ticket.seat_class == Flight.SeatClass.BUSINESS:
                            self.flight.business_seats += 1
                        elif ticket.seat_class == Flight.SeatClass.FIRST_CLASS:
                            self.flight.first_class_seats += 1
                        self.flight.save()
                    elif ticket.direction == ticket.TicketDirection.RETURN and self.return_flight:
                        if ticket.seat_class == Flight.SeatClass.ECONOMY:
                            self.return_flight.economy_seats += 1
                        elif ticket.seat_class == Flight.SeatClass.BUSINESS:
                            self.return_flight.business_seats += 1
                        elif ticket.seat_class == Flight.SeatClass.FIRST_CLASS:
                            self.return_flight.first_class_seats += 1
                        self.return_flight.save()
            elif self.status == self.OrderStatus.BOOKED:
                self.tickets_data = None

            self.status = self.OrderStatus.CANCELLED
            self.save()
        
        return True

    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.flight.flight_number} ({self.get_ticket_type_display()})"

    class Meta:
        db_table = 'order'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'


class Ticket(models.Model):
    class TicketDirection(models.TextChoices):
        OUTBOUND = 'outbound', 'Outbound'
        RETURN = 'return', 'Return'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")
    seat_number = models.CharField(max_length=5)
    seat_class = models.CharField(max_length=20, choices=Flight.SeatClass.choices)
    direction = models.CharField(max_length=10, choices=TicketDirection.choices, default=TicketDirection.OUTBOUND)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def flight(self):
        if self.direction == self.TicketDirection.OUTBOUND:
            return self.order.flight
        return self.order.return_flight

    def __str__(self):
        return f"Ticket {self.id} - {self.seat_number} ({self.seat_class}) - {self.get_direction_display()}"

    class Meta:
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
