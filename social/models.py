from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .custom_manager import CustomUserManager
from django.contrib.postgres.search import SearchVectorField
from django.conf import settings

# Custom user model
class CustomUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('admin', 'Admin'),
    ]
    # Built-in fields you want to include
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    search_vector = SearchVectorField(null=True) 

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        if self.role == 'admin':
            return True
        if self.role == 'write' and perm in ['read', 'write']:
            return True
        if self.role == 'read' and perm == 'read':
            return True
        return False

    def has_module_perms(self, app_label):
        return self.is_staff or self.is_superuser
    
# Friend request model
class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email} : {self.status}"
    

# Block/Unblock model
class Block(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking', on_delete=models.CASCADE)
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"

# User activity model
class UserActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    activity = models.CharField(max_length=255) # Description of the activity
    created_at = models.DateTimeField(auto_now_add=True)  # When the activity was logged

    def __str__(self):
        return f"{self.user.email} - {self.activity} at {self.created_at}"
