# pylint:disable=all
from django.urls import path
from langchainai import views
from django.views.generic import TemplateView

# Wire up our API using automatic URL routing.
urlpatterns = [
    path("", views.HomePage.as_view(), name="entry"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('contact/', views.Contact.as_view(), name='contact'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('error/', TemplateView.as_view(template_name="error.html"), name='error'),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("assistant-files/", views.AssistantFiles.as_view(), name="assistant-files"),
    path("assistant-instructions/", views.AssistantInstructions.as_view(), name="assistant-instructions"),
    path("delete-file/<uuid:file_id>/", views.DeleteAssistantFile.as_view(), name="delete-file"),
    path("upload-file/", views.UploadAssistantFile.as_view(), name="upload-file"),
    path("<str:bot_name>/chat", views.ChatAssistantLobby.as_view(), name="chat-lobby"),
    path("<str:bot_name>/chat/<str:user_name>", views.ChatAssistant.as_view(), name="chat"),
    path("chat-send/", views.ChatSend.as_view(), name="chat-send"),
    path('api/chat/history/', views.ChatHistoryAPI.as_view(), name="chat-history"),
]
