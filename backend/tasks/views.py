import stripe 
import json
import logging
from django.conf import settings
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, Airport, Airline, Airplane, Flight, Order, Ticket
from .serializers import (
    CountrySerializer, AirportSerializer, AirlineSerializer, AirplaneSerializer,
    FlightSerializer, OrderSerializer, TicketSerializer
)
from users.permissions import IsOwnerOrAdmin
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    lookup_field = "slug"


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.select_related("country").all()
    serializer_class = AirportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["country", "city"]
    search_fields = ["name", "city"]
    ordering_fields = ["name", "city"]
    lookup_field = "slug"


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.select_related("airport__country").all()
    serializer_class = AirlineSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["airport"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    lookup_field = "slug"


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airline__airport").all()
    serializer_class = AirplaneSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["airline"]
    search_fields = ["model"]
    ordering_fields = ["model", "capacity"]
    lookup_field = "slug"


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.select_related(
        "airplane", "airplane__airline", "departure_airport", "arrival_airport"
    ).all()
    serializer_class = FlightSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["status", "departure_airport", "arrival_airport", "airplane"]
    search_fields = ["flight_number", "airplane__model", "airplane__airline__name"]
    ordering_fields = ["departure_time", "arrival_time", "flight_number"]
    lookup_field = "flight_number"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("user", "flight", "return_flight").all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["ticket_type", "status", "flight", "return_flight"]
    search_fields = ["flight__flight_number", "return_flight__flight_number"]
    ordering_fields = ["created_at", "total_price"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.select_related("user", "flight", "return_flight").all()
        return Order.objects.filter(user=self.request.user).select_related("user", "flight", "return_flight")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def buy(self, request, pk=None):
        order = self.get_object()
        
        if not (request.user.is_staff or order.user == request.user):
            return Response(
                {"detail": "You don't have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            order.buy()
            serializer = self.get_serializer(order)
            return Response({
                "message": "Order successfully confirmed and tickets issued!",
                "order": serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if not (request.user.is_staff or order.user == request.user):
            return Response(
                {"detail": "You don't have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            order.cancel()
            serializer = self.get_serializer(order)
            return Response({
                "message": "Order successfully cancelled and seats released!",
                "order": serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.select_related("order", "order__flight", "order__return_flight").all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["seat_class", "direction", "order__flight", "order__ticket_type"]
    search_fields = ["seat_number", "order__flight__flight_number"]
    ordering_fields = ["seat_number", "price"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.select_related("order", "order__flight", "order__return_flight").all()
        return Ticket.objects.filter(order__user=self.request.user).select_related("order", "order__flight", "order__return_flight")
    

@api_view(['POST'])
def create_checkout_session(request, id):
    try:
        order = Order.objects.get(id=id, user=request.user)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Order #{order.id} - {order.ticket_type} Ticket',
                    },
                    'unit_amount': int(order.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url="http://127.0.0.1:8000/api/flight/stripe/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://127.0.0.1:8000/api/flight/stripe/cancel",
            metadata={'order_id': order.id}
        )

        return Response({"checkout_url": session.url}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
@api_view(["GET"])
def stripe_success(request):
    session_id = request.GET.get("session_id")
    return Response({"message": "Payment successful!", "session_id": session_id})

@api_view(["GET"])
def stripe_cancel(request):
    return Response({"message": "Payment canceled!"})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    logger.info(f"=== WEBHOOK REQUEST START ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Content-Type: {request.META.get('CONTENT_TYPE')}")
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    logger.info(f"Payload length: {len(payload)}")
    logger.info(f"Signature header: {sig_header}")
    logger.info(f"Webhook secret configured: {bool(endpoint_secret)}")
    
    try:
        payload_str = payload.decode('utf-8')
        logger.info(f"Payload content: {payload_str[:500]}...")  
    except Exception as e:
        logger.error(f"Error decoding payload: {e}")
    
    if not sig_header:
        logger.warning("No signature header - skipping signature verification for testing")
        try:
            event = json.loads(payload)
            logger.info(f"Parsed JSON event successfully: {event.get('type', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            logger.error(f"Payload content: {payload.decode('utf-8', errors='ignore')}")
            return HttpResponse("Invalid JSON", status=400)
    else:
        if not endpoint_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured!")
            return HttpResponse("Webhook secret not configured", status=500)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            logger.info(f"Webhook verified successfully. Event type: {event['type']}")
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return HttpResponse("Invalid payload", status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return HttpResponse("Invalid signature", status=400)

    logger.info(f"Processing event type: {event['type']}")
    
    if event['type'] == 'checkout.session.completed':
        logger.info("Processing checkout.session.completed event")
        session = event['data']['object']
        order_id = session['metadata'].get('order_id')
        
        logger.info(f"Session metadata: {session.get('metadata', {})}")
        logger.info(f"Order ID from metadata: {order_id}")
        
        if not order_id:
            logger.error("No order_id in metadata")
            return HttpResponse("No order_id in metadata", status=400)
            
        try:
            order = Order.objects.get(id=order_id)
            logger.info(f"Found order: {order.id}, status: {order.status}")
            
            if order.status != 'confirmed':
                logger.info(f"Processing order {order_id} - calling buy()")
                order.buy()
                logger.info(f"Order {order_id} confirmed successfully")
            else:
                logger.info(f"Order {order_id} already confirmed")
                
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found in database")
            return HttpResponse(f"Order {order_id} not found", status=404)
        except Exception as e:
            logger.error(f"Error processing order {order_id}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return HttpResponse(f"Error processing order: {str(e)}", status=500)
            
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        order_id = session['metadata'].get('order_id')
        logger.info(f"Checkout session expired for order {order_id}")
        
    elif event['type'] == 'payment_intent.payment_failed':
        logger.error(f"Payment failed: {event['data']['object']}")
    else:
        logger.info(f"Unhandled event type: {event['type']}")

    logger.info(f"=== WEBHOOK REQUEST END ===")
    return HttpResponse("OK", status=200)