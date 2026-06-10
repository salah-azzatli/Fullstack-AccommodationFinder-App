# payments/admin.py
from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ["id", "booking", "payment_type", "payment_method", "amount_cents", "status", "paid_at"]
    list_filter   = ["status", "payment_type", "payment_method"]
    search_fields = ["booking__tenant__username", "transaction_id", "paymob_order_id"]
    readonly_fields = ["raw_response", "created_at", "updated_at"]