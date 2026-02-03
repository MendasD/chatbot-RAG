"""
URLs pour l'application Chat
"""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Pages principales
    path('', views.chat_home, name='home'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),

    # API endpoints
    path('api/conversation/create/', views.create_conversation, name='create_conversation'),
    path('api/conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('api/conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/conversation/<int:conversation_id>/history/', views.conversation_history, name='conversation_history'),

    # Feedback
    path('api/message/<int:message_id>/feedback/', views.submit_feedback, name='submit_feedback'),

    # Utilitaires
    path('api/suggestions/', views.get_suggestions, name='get_suggestions'),
    path('api/publications/search/', views.search_publications, name='search_publications'),
]
