## messaging app overview ##


# ────────────────────────Start URL─────────────────────────────────────

```
from django.urls import path
from .views import (
    ConversationView,
    MessageView,
)

urlpatterns = [
    path("",                       ConversationView.as_view(),  name="conversations"),
    path("<int:conversation_id>/", MessageView.as_view(),   name="messages"),
]     
```

# ────────────────────────End URL───────────────────────────────────────



# ────────────────────────Start Serializer──────────────────────────────

```




from rest_framework import serializers

from messaging.models import Conversation, Message
from accounts.models import Users
from bookings.models import Booking
 




class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True) #
    
    class Meta:
        model  = Message
        fields = ["id", "conversation", "sender", "sender_name", "body", "is_read", "created_at"]
        read_only_fields = fields

#────────────────────────────────────────────────────────────────────────────────────────────

class ConversationSerializer(serializers.ModelSerializer):
    last_message  = serializers.SerializerMethodField()# why i need the last message 
    unread_count  = serializers.SerializerMethodField()
    other_user    = serializers.SerializerMethodField()

    class Meta:
        model  = Conversation
        fields = ["id", "initiator", "receiver", "booking", "property",
                  "other_user", "last_message", "unread_count", "created_at", "updated_at"]
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if not msg:
            return None
        return {"body": msg.body, "created_at": msg.created_at, "sender": msg.sender_id}# sender_id from where

    def get_unread_count(self, obj):#we have in view??
        user = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_user(self, obj):
        user = self.context["request"].user
        other = obj.receiver if obj.initiator == user else obj.initiator
        return {"id": other.id, "name": other.get_full_name(), "profile_picture": str(other.profile_picture) if other.profile_picture else None}

#────────────────────────────────────────────────────────────────────────────────────────────

class StartConversationSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    booking_id  = serializers.IntegerField(required=False)
    message     = serializers.CharField()

    def validate_receiver_id(self, value):
        try:
            Users.objects.get(id=value)
        except Users.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value
```

# ────────────────────────End Serializer────────────────────────────────




# ────────────────────────Start View────────────────────────────────────

```




from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from messaging.models import Conversation, Message
from accounts.models import Users
from bookings.models import Booking
from api.messaging_api.serializers import (
    ConversationSerializer,
    MessageSerializer,
    StartConversationSerializer,
)



class ConversationView(APIView):
    """
    GET  /api/messages/  → list all my conversations
    POST /api/messages/  → start a new conversation (or return existing one)
 
    Both methods live on the same view so they share one URL cleanly.
    Django routes to get() or post() based on the HTTP method.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            Q(initiator=request.user) | Q(receiver=request.user)
        ).prefetch_related("messages")
        serializer = ConversationSerializer(conversations, many=True, context={"request": request})
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        receiver_id = serializer.validated_data.get("receiver_id")
        receiver    = Users.objects.get(id=receiver_id)
        booking_id  = serializer.validated_data.get("booking_id")
        booking     = Booking.objects.get(id=booking_id) if booking_id else None

         # Return existing conversation if one already exists for this pai
        conv = Conversation.objects.filter(
            Q(initiator=request.user, receiver=receiver) |
            Q(initiator=receiver,     receiver=request.user),
            booking=booking
        ).first()

        if not conv:
            conv = Conversation.objects.create(
                initiator=request.user,
                receiver=receiver,
                booking=booking,
                property=booking.property if booking else None,
            )

        # Create first message
        Message.objects.create(
            conversation=conv,
            sender=request.user,
            body=serializer.validated_data.get("message"),
        )

        return Response(
            ConversationSerializer(conv, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


#────────────────────────────────────────────────────────────────────────────────────────────

class MessageView(APIView):
    """
    GET /api/messages/<id>/ — load conversation history + mark messages read.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conv = Conversation.objects.get(
                Q(initiator=request.user) | Q(receiver=request.user),
                id=conversation_id,
            )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

        # Mark all messages from the other person as read
        conv.messages.exclude(sender=request.user).update(is_read=True)

        messages   = conv.messages.select_related("sender")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


    
    
```

# ────────────────────────End View──────────────────────────────────────







# ────────────────────────Start Model────────────────────────────────────

```



from django.db import models

from accounts.models import Users
from bookings.models import Booking
from properties.models import Property



class Conversation(models.Model):
    """
    A conversation between two users.
    Can be standalone (DM) or linked to a booking/property.

    booking=None  → standalone DM
    booking=<id>  → linked to a specific booking (tenant ↔ landlord)
    """
    initiator = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="initiated_conversations")
    receiver  = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="received_conversations")

    booking  = models.ForeignKey(Booking,  on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            # Prevent duplicate conversations for the same pair + booking
            models.UniqueConstraint(
                fields=["initiator", "receiver", "booking"],
                name="unique_conversation_per_booking",
            )
        ]

    def __str__(self):
        return f"{self.initiator.username} ↔ {self.receiver.username} ({self.booking or 'DM'})"
    
 
#─────────────────────────────────────────────────────────────────────────────────────────────────────────────

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender       = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="sent_messages")

    body    = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.body[:40]}"

```

# ────────────────────────End Model──────────────────────────────────────

