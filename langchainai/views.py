# pylint:disable=all
import os
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import Message, Profile, CustomerMessage
from pinecone_plugins.assistant.models.chat import Message as PineConeMessage
from django.views import View
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from pinecone import Pinecone
from django.shortcuts import get_object_or_404

def get_assistant(assistant_name, pinecone_api_key):
    pinecone_client = Pinecone(api_key=pinecone_api_key)
    try:
        return pinecone_client.assistant.Assistant(
            assistant_name=assistant_name,
        )
    except Exception as error:
        print("Error", error)
        try:
            return pinecone_client.assistant.create_assistant(
                assistant_name=assistant_name,
                instructions="Do not answer anything which is not relavent to the uploaded data, do not use your common sense to answer general questions",  # Description or directive for the assistant to apply to all responses.
                region="us",  # Region to deploy assistant. Options: "us" (default) or "eu".
                timeout=30,  # Maximum seconds to wait for assistant status to become "Ready" before timing out.
            )
        except:
            redirect("error")

class HomePage(View):
    def get(self, request):
        return render(request, "landing.html")
class Contact(View):
    def get(self, request):
        return render(request, "contact.html")

class ChatHistoryAPI(APIView):
    def post(self, request):
        user_name = request.data.get("user_name")
        past_messages = CustomerMessage.objects.filter(user_name=user_name).order_by("-timestamp")[:25]
        past_messages = list(reversed(past_messages))

        messages = [{"role": msg.role, "text": msg.text, "time" : msg.timestamp} for msg in past_messages]
        return Response({"messages": messages}, status=200)

class ChatAssistantLobby(View):
    def get(self, request,bot_name, user_name=None):
        if not bot_name:
            return HttpResponse("Unknown assistant")
        try:
            user = get_object_or_404(User, username=bot_name)
        except Http404:
            return HttpResponse("Please contact admin")
        if not user:
            return HttpResponse("Please contact admin")
        profile = Profile.objects.get(user=user)
        if not profile:
            return HttpResponse("Please contact admin")
        if not profile.pinecone_api_key:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        data = {
            "bot_name" : user.username,
            "user_name" : user_name
        }
        if user_name:
            return render(request, "chat.html", data)
        return render(request, "chat-lobby.html", data)
    
class ChatSend(APIView):
    def post(self, request):
        username = request.data.get("user_name")
        user_message = request.data.get("message")
        botname = request.data.get("botname")
        if not user_message:
            return Response(
                {"error": "Message is required"}, status=400
            )
        CustomerMessage.objects.create(user_name=username, role="human", text=user_message)
        past_messages = CustomerMessage.objects.filter(user_name=username).order_by("-timestamp")[
            :10
        ]  # Get latest 10
        past_messages = list(reversed(past_messages))
        conversation_history = [(msg.role, msg.text) for msg in past_messages]
        try:
            profile = Profile.objects.get(namespace=botname)
            if not profile:
                return Response(
                    {
                        "response" : "Internal erroor"
                    }
                )
            pinecone_assistant = get_assistant(
                assistant_name=botname,
                pinecone_api_key=profile.pinecone_api_key
            )
            chat_context = [PineConeMessage(role="user" if msg.role == "human" else "assistant", content=msg.text) for msg in past_messages]
            response = pinecone_assistant.chat_completions(messages=chat_context)
            print("Assitant response", response)
            text_response = response.get("choices")[0].get("message").get("content")
            print("Text response", text_response)
            CustomerMessage.objects.create(user_name=username, role="ai", text=text_response)
            return Response(
                {"response": text_response}, status=200
            )
        except Exception as e:
            print("Error", e)
            raise ValueError(
                "Api key issue"
            )
    
class ChatAssistant(View):
    def get(self, request,bot_name, user_name=None):
        if not bot_name:
            return HttpResponse("Unknown assistant")
        try:
            user = get_object_or_404(User, username=bot_name)
        except Http404:
            return HttpResponse("Please contact admin")
        if not user:
            return HttpResponse("Please contact admin")
        profile = Profile.objects.get(user=user)
        if not profile:
            return HttpResponse("Please contact admin")
        if not profile.pinecone_api_key:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        data = {
            "bot_name" : user.username,
            "user_name" : user_name
        }
        if user_name:
            return render(request, "chat.html",data)
        return render(request, "chat-lobby.html", data)

class AssistantInstructions(LoginRequiredMixin, View):
    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        if not profile:
            return Response({"messages": "Profile not found"}, status=400)
        if not profile.pinecone_api_key:
            return HttpResponse("API key not found")
        pinecone_assistant = get_assistant(
            assistant_name=request.user.username,
            pinecone_api_key=profile.pinecone_api_key,
        )
        if pinecone_assistant is None:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        data = {"instruction": pinecone_assistant.instructions}
        return render(request, "assistant_instructions.html", data)

    def post(self, request):
        new_instruction = request.POST.get("instruction", "")
        profile = Profile.objects.get(user=request.user)
        pinecone_client = Pinecone(api_key=profile.pinecone_api_key)
        if pinecone_client is None:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        updateassistant = pinecone_client.assistant.update_assistant(
            assistant_name=request.user.username, 
            instructions=new_instruction,
        )
        return redirect("assistant-instructions")


class UploadAssistantFile(View):
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        uploaded_file = request.FILES["file"]
        pinecone_client = Pinecone(api_key=profile.pinecone_api_key)
        pinecone_assistant = pinecone_client.assistant.Assistant(
            assistant_name=profile.namespace,
        )
        if pinecone_assistant is None:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        file_path = f"/tmp/{uploaded_file.name}"  # Adjust path if necessary
        with open(file_path, "wb") as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
        print("loacal write completed")
        response = pinecone_assistant.upload_file(file_path=file_path, timeout=None)
        print("Upload to api done")
        return JsonResponse({"message": "File uploaded successfully!"})


class DeleteAssistantFile(View):
    def post(self, request, file_id):
        profile = Profile.objects.get(user=request.user)
        pinecone_assistant = get_assistant(
            assistant_name=request.user.username,
            pinecone_api_key=profile.pinecone_api_key
        )
        if pinecone_assistant is None:
            return HttpResponse("Please configure the API key correctly, if the problem still not solved contact admin")
        pinecone_assistant.delete_file(file_id=str(file_id))
        messages.success(request, "File deleted successfully!")
        return redirect("assistant-files")


class AssistantFiles(LoginRequiredMixin, View):
    def get(self, request):
        profile = Profile.objects.get(user=request.user)

        if not profile:
            return HttpResponse("Profile not found")
        if not profile.user.username:
            return render(request, "error.html", {"message" : "Please configure the username correctly, if the problem still not solved contact admin"})
        if not profile.pinecone_api_key:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        pinecone_assistant = get_assistant(
            assistant_name=request.user.username,
            pinecone_api_key=profile.pinecone_api_key
        )
        if pinecone_assistant is None:
            return render(request, "error.html", {"message" : "Please configure the API key correctly, if the problem still not solved contact admin"})
        files = pinecone_assistant.list_files()
        files = [file.to_dict() for file in files]
        data = {"all_files": files}
        return render(request, "assistant.html", data)


class LogoutView(View):
    def post(self, request):
        logout(request)  # Logs out the user
        return redirect("login")  # Redirect to login page



class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)

        # Pass profile data to template
        context = {
            "namespace": request.user.username,
            "openai_key": profile.openai_api_key,
            "pinecone_key": profile.pinecone_api_key,
        }
        return render(request, "profile.html", context)

    def post(self, request):
        try:
            namespace = request.POST.get("namespace")
            openai_key = request.POST.get("openai_key")
            pinecone_key = request.POST.get("pinecone_key")
            user = request.user

            # Get or create the Profile instance
            profile, created = Profile.objects.get_or_create(user=user)

            # Update the profile fields
            profile.namespace = user.username
            profile.openai_api_key = openai_key or profile.openai_api_key
            profile.pinecone_api_key = pinecone_key or profile.pinecone_api_key
            profile.save()

            return redirect("profile")

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class DashboardView(LoginRequiredMixin, View):
    login_url = "/login/"  # Redirect to login page if not authenticated
    redirect_field_name = "next"  # Redirect back after login

    def get(self, request):
        return render(request, "dashboard.html")


class SignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "signup.html")  # Render template with empty form

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return render(request, "signup.html")

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "signup.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "signup.html")

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password1
        )
        Profile.objects.get_or_create(user=user)
        login(request, user)  # Auto login after signup
        messages.success(request, "Signup successful!")
        return redirect("dashboard")  # Redirect to dashboard


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "login.html")  # Render the login page

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Validate input fields
        if not username or not password:
            messages.error(request, "All fields are required.")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("dashboard")  # Redirect to dashboard
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "login.html")
