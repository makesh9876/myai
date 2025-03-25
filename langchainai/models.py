#pylint:disable=all
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Message(models.Model):
    ROLE_CHOICES = [
        ("human", "Human"),
        ("ai", "AI"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to Django user
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)  # Who sent the message
    text = models.TextField()  # Message content
    timestamp = models.DateTimeField(auto_now_add=True)  # Message time

    class Meta:
        ordering = ["timestamp"]  # Sort messages by time

    def __str__(self):
        return f"{self.user.username} ({self.role}): {self.text[:50]}"
    

class KeyConfiguration(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    namespace = models.CharField(max_length=100, unique=True, blank=True, null=True)
    openai_api_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    pinecone_api_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    # enable_console_chat = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return self.user.username
    

class CustomerMessage(models.Model):
    ROLE_CHOICES = [
        ("human", "Human"),
        ("ai", "AI"),
    ]
    user_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)  # Who sent the message
    text = models.TextField()  # Message content
    timestamp = models.DateTimeField(auto_now_add=True)  # Message time

    class Meta:
        ordering = ["timestamp"]  # Sort messages by time

    def __str__(self):
        return f"{self.user_name} ({self.role}): {self.text[:50]}"