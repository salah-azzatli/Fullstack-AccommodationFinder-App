from django.contrib import admin
from messaging.models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "initiator", "receiver", "booking", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("initiator__username", "receiver__username")
    ordering = ("-updated_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "body", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("body", "sender__username")
    ordering = ("-created_at",)