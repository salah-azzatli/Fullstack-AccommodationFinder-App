from django.urls import path
from .views import (
    InitiateDepositView,
    PayRemainingOnlineView,
    MarkRemainingOfflineView,
    MyPaymentsView,
    PaymobWebhookView,
)

urlpatterns = [
    path("deposit/",           InitiateDepositView.as_view(),     name="pay-deposit"),
    path("remaining/online/",  PayRemainingOnlineView.as_view(),  name="pay-remaining-online"),
    path("remaining/offline/", MarkRemainingOfflineView.as_view(),name="pay-remaining-offline"),
    path("my/",                MyPaymentsView.as_view(),          name="my-payments"),
    path("webhook/",           PaymobWebhookView.as_view(),       name="paymob-webhook"),
]