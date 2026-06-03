from django.urls import path
from api.messaging_api.views import (
    ConversationView,
    MessageListView,
)

urlpatterns = [
    path("",                       ConversationView.as_view(),  name="conversations"),
    path("<int:conversation_id>/", MessageListView.as_view(),   name="messages"),
]