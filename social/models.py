from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .custom_manager import CustomUserManager

# Create your models here.
class CustomUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True, max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

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