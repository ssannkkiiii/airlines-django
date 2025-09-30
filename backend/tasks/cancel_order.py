from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Order

@shared_task
def cancel_unpaid_order(order_id):
    try:
        order = Order.objects.get(id=order_id)
        if order.status == Order.OrderStatus.BOOKED:
            if order.created_at <= timezone.now() - timedelta(minutes=1):
                order.status = Order.OrderStatus.CANCELED
                order.save()
    except Order.DoesNotExist:
        pass
