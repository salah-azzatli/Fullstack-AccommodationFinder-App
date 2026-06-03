from django.urls import re_path
from messaging.consumers import ChatConsumer


# The client connects to: ws://localhost:8000/ws/chat/<conversation_id>/?token=<jwt>

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<conversation_id>\d+)/$", ChatConsumer.as_asgi()),
]