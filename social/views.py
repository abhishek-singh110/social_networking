from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import SignUpSerializer, LoginSerializer
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

# Create your views here.
def generate_strong_password(length=12):
        """Generate a strong password."""
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(length))
        return password


class SignUpView(APIView):
    def post(self, request):
        email = request.data.get('email')

        # Generate a strong password
        password = generate_strong_password()

        # Create user using the serializer
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(password=password)  # Pass the generated password
            # Send email with the generated password
            # send_mail(
            #     'Your Account Created',
            #     f'Your account has been created successfully. Your password is: {password}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     [email],
            #     fail_silently=False,
            # )
            return Response({'message': 'User created successfully. Check your email for the password.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.utils.decorators import method_decorator
class LoginView(APIView):
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].lower()
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None:
                # Generate JWT tokens (access and refresh)
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                return Response({
                    'message': 'Login successful!',
                    'access_token': str(access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



from .permissions import RoleBasedPermission

class SomeProtectedView(APIView):
    permission_classes = [RoleBasedPermission]

    def get(self, request):
        # Handle read access
        return Response({'message': 'You have access to read data.'}, status=status.HTTP_200_OK)

    def post(self, request):
        # Handle write access
        return Response({'message': 'Data has been written.'}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        # Handle delete access
        return Response({'message': 'Data has been deleted.'}, status=status.HTTP_204_NO_CONTENT)
