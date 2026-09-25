from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messaging.inbox'),
    path('start/<int:user_id>/', views.start_conversation, name='messaging.start'),
    path('<int:conversation_id>/', views.conversation_detail, name='messaging.conversation'),
    path(
        '<int:conversation_id>/updates/',
        views.conversation_updates,
        name='messaging.conversation_updates',
    ),
]
