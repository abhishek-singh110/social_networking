from rest_framework import serializers
from .models import CustomUser, FriendRequest
from django.core.validators import RegexValidator

# Custom validator for password
password_regex_validator = RegexValidator(
    regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[*@&#$])[A-Za-z\d@$!%*#?&]{8,}$',
    message="Password must be at least 8 characters long, contain at least one uppercase letter, one special character, and one digit."
)

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[password_regex_validator])

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def create(self, validated_data):
        email = validated_data['email'].lower()
        # Extract the first name from the email before the '@'
        first_name = email.split('@')[0]
        
        user = CustomUser(
            email=email,
            first_name=first_name  # Set first_name to the part before '@'
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['sender', 'receiver', 'status']
