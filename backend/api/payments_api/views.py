import json
import hmac
import hashlib

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from bookings.models import Booking
from payments.models import Payment
from payments.paymob import PaymobService
from .serializers import (
    PaymentSerializer,
    InitiateDepositSerializer,
    PayRemainingSerializer,
    MarkOfflineSerializer,
)


class InitiateDepositView(APIView):
    """
    Step 1 of payment flow.
    Student initiates deposit
    
    the overview flow of the whole payment proccess is :
        Create Intention
            ↓
        Redirect User
            ↓
        Payment Happens
            ↓
        Webhook Arrives
            ↓
        Verify HMAC
            ↓
        Update Database
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiateDepositSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        booking = Booking.objects.get(id=serializer.validated_data["booking_id"])

        billing_data = {
            "first_name":      request.user.first_name or "NA",
            "last_name":       request.user.last_name  or "NA",
            "email":           request.user.email,
            "phone_number":    serializer.validated_data["phone"],
            "apartment":       "NA",
            "floor":           "NA",
            "street":          "NA",
            "building":        "NA",
            "shipping_method": "NA",
            "postal_code":     "NA",
            "city":            "NA",
            "country":         "EG",
            "state":           "NA",
        }

        try:
                     #Create Payment Intention
            result = PaymobService.initiate_payment(
                amount_cents = booking.deposit_amount_cents,
                billing_data = billing_data,
            )

            Payment.objects.create(
                booking         = booking,
                payment_type    = Payment.PaymentType.DEPOSIT,
                payment_method  = Payment.PaymentMethod.ONLINE,
                amount_cents    = booking.deposit_amount_cents,
                paymob_order_id = str(result["order_id"]),
                status          = Payment.Status.PENDING,
            )

            return Response(result)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

#──────────────────────────────────────────────────────────────────────────────────────────────────────

class PayRemainingOnlineView(APIView):
    """Student pays remaining amount online via Paymob."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PayRemainingSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        booking = Booking.objects.get(id=serializer.validated_data["booking_id"])

        billing_data = {
            "first_name":      request.user.first_name or "NA",
            "last_name":       request.user.last_name  or "NA",
            "email":           request.user.email,
            "phone_number":    serializer.validated_data["phone"],
            "apartment":       "NA",
            "floor":           "NA",
            "street":          "NA",
            "building":        "NA",
            "shipping_method": "NA",
            "postal_code":     "NA",
            "city":            "NA",
            "country":         "EG",
            "state":           "NA",
        }

        try:
            result = PaymobService.initiate_payment(
                amount_cents = booking.remaining_amount_cents,
                billing_data = billing_data,
            )

            Payment.objects.create(
                booking         = booking,
                payment_type    = Payment.PaymentType.REMAINING,
                payment_method  = Payment.PaymentMethod.ONLINE,
                amount_cents    = booking.remaining_amount_cents,
                paymob_order_id = str(result["order_id"]),
                status          = Payment.Status.PENDING,
            )

            return Response(result)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


#──────────────────────────────────────────────────────────────────────────────────────────────────────

class MarkRemainingOfflineView(APIView):
    """Landlord marks remaining amount as paid in cash."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MarkOfflineSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        booking = Booking.objects.get(id=serializer.validated_data["booking_id"])

        with transaction.atomic():
            Payment.objects.create(
                booking        = booking,
                payment_type   = Payment.PaymentType.REMAINING,
                payment_method = Payment.PaymentMethod.OFFLINE,
                amount_cents   = booking.remaining_amount_cents,
                status         = Payment.Status.COMPLETED,
                paid_at        = timezone.now(),
            )

            booking.status = "completed"
            booking.save()

        return Response({"message": "Cash payment recorded. Booking marked as completed."})


#──────────────────────────────────────────────────────────────────────────────────────────────────────


class MyPaymentsView(APIView):
    """Student views all their payments."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(
            booking__tenant=request.user
        ).select_related("booking")

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


#──────────────────────────────────────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class PaymobWebhookView(View):
    """
    Paymob calls this after every transaction.
    Flow: verify HMAC → update Payment → update Booking.

    the idea of HMAC is to make new HMAC based on data i have and 
    make sure that it match the received hmac  
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
        except Exception:
            return HttpResponse(status=400)

        received_hmac = request.GET.get("hmac", "")
        # Step 1: verify this is really from Paymob
        if not self._verify_hmac(data, received_hmac):
            return HttpResponse("Invalid HMAC", status=403)

        obj            = data.get("obj", {})
        order_id       = str(obj.get("order", {}).get("id", ""))
        success        = obj.get("success", False)
        transaction_id = str(obj.get("id", ""))

        # Step 2: find the payment record
        try:
            payment = Payment.objects.select_related("booking__property").get(
                paymob_order_id=order_id
            )
        except Payment.DoesNotExist:
            return HttpResponse(status=404)

        # Step 3: idempotency — ignore if already processed
        if payment.status == Payment.Status.COMPLETED:
            return HttpResponse(status=200)

        # Step 4: update payment + booking atomically
        with transaction.atomic():
            if success:
                payment.status         = Payment.Status.COMPLETED
                payment.transaction_id = transaction_id
                payment.raw_response   = obj
                payment.paid_at        = timezone.now()
                payment.save()

                booking = payment.booking
                if payment.payment_type == Payment.PaymentType.DEPOSIT:
                    booking.status = "deposit_paid"
                elif payment.payment_type == Payment.PaymentType.REMAINING:
                    booking.status = "completed"
                booking.save()

            else:
                payment.status         = Payment.Status.FAILED
                payment.failure_reason = obj.get("data", {}).get("message", "")
                payment.raw_response   = obj
                payment.save()

        return HttpResponse(status=200)

    def _verify_hmac(self, data ,received_hmac):
        """Verify Paymob HMAC signature."""
        obj           = data.get("obj", {})

        def fmt(value):
            """Convert Python booleans to lowercase — Paymob expects true/false not True/False"""
            if isinstance(value, bool):
                return "true" if value else "false"
            if value is None:
                return ""
            return str(value)
        fields = [
            fmt(obj.get("amount_cents",           "")),
            fmt(obj.get("created_at",             "")),
            fmt(obj.get("currency",               "")),
            fmt(obj.get("error_occured",          "")),
            fmt(obj.get("has_parent_transaction", "")),
            fmt(obj.get("id",                     "")),
            fmt(obj.get("integration_id",         "")),
            fmt(obj.get("is_3d_secure",           "")),
            fmt(obj.get("is_auth",                "")),
            fmt(obj.get("is_capture",             "")),
            fmt(obj.get("is_refunded",            "")),
            fmt(obj.get("is_standalone_payment",  "")),
            fmt(obj.get("is_voided",              "")),
            fmt(obj.get("order", {}).get("id",    "")),
            fmt(obj.get("owner",                  "")),
            fmt(obj.get("pending",                "")),
            fmt(obj.get("source_data", {}).get("pan",      "")),
            fmt(obj.get("source_data", {}).get("sub_type", "")),
            fmt(obj.get("source_data", {}).get("type",     "")),
            fmt(obj.get("success",                "")),
        ]


        expected = hmac.new(
            settings.PAYMOB_HMAC_SECRET.encode(),
            "".join(fields).encode(),
            hashlib.sha512
        ).hexdigest()

        
        return hmac.compare_digest(expected, received_hmac)