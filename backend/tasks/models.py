from django.db import models
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
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name="airplanes")

    economy_seats = models.PositiveIntegerField(default=0, help_text="Number of economy class seats")
    business_seats = models.PositiveIntegerField(default=0, help_text="Number of business class seats")
    first_class_seats = models.PositiveIntegerField(default=0, help_text="Number of first class seats")
    
    rows_economy = models.PositiveIntegerField(default=0, help_text="Number of rows in economy class")
    seats_per_row_economy = models.PositiveIntegerField(default=6, help_text="Seats per row in economy class")
    rows_business = models.PositiveIntegerField(default=0, help_text="Number of rows in business class")
    seats_per_row_business = models.PositiveIntegerField(default=4, help_text="Seats per row in business class")
    rows_first_class = models.PositiveIntegerField(default=0, help_text="Number of rows in first class")
    seats_per_row_first_class = models.PositiveIntegerField(default=2, help_text="Seats per row in first class")
    
    def __str__(self):
        return f"Airplane {self.model} of {self.airline.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:  
            self.slug = slugify(self.model)        
        super().save(*args, **kwargs)
        
    def get_total_seats(self):
       return self.economy_seats + self.business_seats + self.first_class_seats
    
    def get_seat_configuration(self):
        return {
            'economy': {
                'rows': self.rows_economy,
                'seats_per_row': self.seats_per_row_economy,
                'total_seats': self.economy_seats
            },
            'business': {
                'rows': self.rows_business,
                'seats_per_row': self.seats_per_row_business,
                'total_seats': self.business_seats
            },
            'first_class': {
                'rows': self.rows_first_class,
                'seats_per_row': self.seats_per_row_first_class,
                'total_seats': self.first_class_seats
            }
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
    
    flight_number = models.CharField(max_length=10, unique=True)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="flights")
    departure_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="departures")
    arrival_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="arrivals")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=FlightStatus.choices, 
        default=FlightStatus.SCHEDULED,
        verbose_name='Flight status'    
    )

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.city} -> {self.arrival_airport.city}"
    
    def get_available_seats(self, seat_class=None):
        
        seats = Seat.objects.filter(airplane=self.airplane)        
        if seat_class:
            seats = seats.filter(seat_class=seat_class)
        
        occupied_seats = Ticket.objects.filter(
            flight=self,
            status__in=[
                Ticket.TicketStatus.BOOKED,
                Ticket.TicketStatus.PAID,
                Ticket.TicketStatus.USED
            ]
        ).values_list("seat_id", flat=True)

        return seats.exclude(id__in=occupied_seats)

    
    def get_seat_availability_summary(self):
        summary = {}
        for seat_class, _ in Seat.SeatClass.choices:
            available = self.get_available_seats(seat_class).count()
            total = Seat.objects.filter(airplane=self.airplane, seat_class=seat_class).count()
            summary[seat_class] = {
                'available': available,
                'total': total,
                'occupied': total - available
            }
        return summary
    
    class Meta:
        db_table = 'flight'
        verbose_name = 'Flight'
        verbose_name_plural = 'Flights'
        
class Seat(models.Model):
    class SeatClass(models.TextChoices):
        ECONOMY = 'economy', 'Economy'
        BUSINESS = 'business', 'Business'
        FIRST_CLASS = 'first_class', 'First Class'
    
    class SeatStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        OCCUPIED = 'occupied', 'Occupied'
        MAINTENANCE = 'maintenance', 'Maintenance'
        BLOCKED = 'blocked', 'Blocked'
    
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=10, help_text="Seat number (e.g., 1A, 12C)")
    seat_class = models.CharField(
        max_length=20,
        choices=SeatClass.choices,
        default=SeatClass.ECONOMY,
        verbose_name='Seat Class'
    )
    row_number = models.PositiveIntegerField(help_text="Row number")
    seat_letter = models.CharField(max_length=2, help_text="Seat letter (A, B, C, etc.)")
    status = models.CharField(
        max_length=20,
        choices=SeatStatus.choices,
        default=SeatStatus.AVAILABLE,
        verbose_name='Seat Status'
    )
    is_window_seat = models.BooleanField(default=False, help_text="Is this a window seat?")
    is_aisle_seat = models.BooleanField(default=False, help_text="Is this an aisle seat?")
    is_emergency_exit = models.BooleanField(default=False, help_text="Is this an emergency exit seat?")
    extra_legroom = models.BooleanField(default=False, help_text="Does this seat have extra legroom?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.seat_number} ({self.get_seat_class_display()}) - {self.airplane.model}"
    
    def save(self, *args, **kwargs):
        if not self.seat_number:
            self.seat_number = f"{self.row_number}{self.seat_letter}"
        
        if not self.is_window_seat and not self.is_aisle_seat:
            self._detect_seat_type()
        
        super().save(*args, **kwargs)
    
    def _detect_seat_type(self):
        config = self.airplane.get_seat_configuration()
        class_config = config.get(self.seat_class, {})
        seats_per_row = class_config.get('seats_per_row', 6)
        
        if seats_per_row == 6:  
            if self.seat_letter in ['A', 'F']:
                self.is_window_seat = True
            elif self.seat_letter in ['C', 'D']:
                self.is_aisle_seat = True
        elif seats_per_row == 4:  
            if self.seat_letter in ['A', 'D']:
                self.is_window_seat = True
            elif self.seat_letter in ['B', 'C']:
                self.is_aisle_seat = True
        elif seats_per_row == 2: 
            if self.seat_letter in ['A', 'B']:
                self.is_window_seat = True
    
    def is_available(self, flight=None):
        if self.status != self.SeatStatus.AVAILABLE:
            return False
        
        if flight:
            return not Ticket.objects.filter(
                flight=flight,
                seat_number=self.seat_number,
                status__in=[Ticket.TicketStatus.BOOKED, Ticket.TicketStatus.PAID, Ticket.TicketStatus.USED]
            ).exists()
        
        return True
    
    class Meta:
        db_table = 'seat'
        verbose_name = 'Seat'
        verbose_name_plural = 'Seats'
        unique_together = ['airplane', 'seat_number']
        ordering = ['row_number', 'seat_letter']

class Ticket(models.Model):
    class TicketStatus(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        USED = 'used', 'Used'
    
    class TicketType(models.TextChoices):
        ONE_WAY = 'one_way', 'One Way'
        ROUND_TRIP = 'round_trip', 'Round Trip'
        MULTI_CITY = 'multi_city', 'Multi City'

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    seat_number = models.CharField(max_length=5)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=TicketStatus.choices, 
        default=TicketStatus.BOOKED
    )
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices,
        default=TicketType.ONE_WAY,
        verbose_name='Ticket Type'
    )
    return_flight = models.ForeignKey(
        Flight, 
        on_delete=models.CASCADE, 
        related_name="return_tickets",
        null=True, 
        blank=True,
        verbose_name='Return Flight'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):        
        if self.ticket_type == self.TicketType.ROUND_TRIP and not self.return_flight:
            raise ValidationError({
                'return_flight': 'Return flight is required for round trip tickets.'
            })
        
        if self.ticket_type == self.TicketType.ONE_WAY and self.return_flight:
            raise ValidationError({
                'return_flight': 'Return flight should not be specified for one way tickets.'
            })
        
        if self.return_flight and self.return_flight == self.flight:
            raise ValidationError({
                'return_flight': 'Return flight must be different from outbound flight.'
            })
        
        if self.return_flight and self.return_flight.departure_time <= self.flight.arrival_time:
            raise ValidationError({
                'return_flight': 'Return flight departure must be after outbound flight arrival.'
            })
    
    
    @property
    def is_one_way(self):
        return self.ticket_type == self.TicketType.ONE_WAY
    
    @property
    def is_round_trip(self):
        return self.ticket_type == self.TicketType.ROUND_TRIP
    
    @property
    def is_multi_city(self):
        return self.ticket_type == self.TicketType.MULTI_CITY
    
    @property
    def total_price(self):
        if self.is_round_trip and self.return_flight:
            return self.price * 2
        return self.price

    def __str__(self):
        ticket_type_display = self.get_ticket_type_display()
        return f"Ticket {self.id} - {self.user.email} - {self.flight.flight_number} ({ticket_type_display})"
    
    class Meta:
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        unique_together = ("flight", "seat") 


class Order(models.Model):
    
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'
        FAILED = 'failed', 'Failed'
        
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='orders')
    seat_class = models.CharField(max_length=20, null=True, blank=True)
    seat_preference = models.CharField(max_length=20, null=True, blank=True, help_text="'window'|'aisle'|'any'")
    seat = models.ForeignKey(Seat, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    seat_number = models.CharField(max_length=10, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.flight.flight_number}"
    
    class Meta:
        db_table = "order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        
    def allocate_seat(self):
        
        available_seats = self.flight.get_available_seats(seat_class=self.seat_class)
        
        if self.seat_preference == "window":
            available_seats = available_seats.filter(is_window_seat=True)
        elif self.seat_preference == 'aisle':
            available_seats = available_seats.filter(is_aisle_seat=True)
            
        seat = available_seats.first()
        if not seat:
            raise ValidationError("No available seats for your preferences.")

        self.seat = seat 
        self.seat_number = seat.seat_number
        
        base_price = 100.0
        if self.seat_class == "business":
            base_price = 300.0
        elif self.seat_class == "first_class":
            base_price = 600.0

        self.price = base_price
        self.save()
        return self
    
    def pay(self):
        if self.status != self.OrderStatus.PENDING:
            raise ValidationError("Only pending orders can be paid.")
        if not self.seat:
            raise ValidationError("Order has no allocated seat.")
        
        ticket = Ticket.objects.create(
            flight=self.flight,
            user=self.user,
            seat=self.seat,
            seat_number=self.seat_number,
            price=self.price,
            status=Ticket.TicketStatus.PAID,
        )
        
        self.status = self.OrderStatus.PAID 
        self.save(update_fields=["status"])
        return ticket 
    
    def cancel(self):
        if self.status not in [self.OrderStatus.PENDING, self.OrderStatus.FAILED]:
            raise ValidationError("Only pending or failed orders can be cancelled.")
        
        self.status = self.OrderStatus.CANCELLED
        self.seat = None 
        self.seat_number = None
        self.save(update_fields=["status", "seat", "seat_number"])
        return self 