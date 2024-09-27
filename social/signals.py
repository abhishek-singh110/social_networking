from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from .models import CustomUser  # Adjust this import based on your project structure

@receiver(post_save, sender=CustomUser)
def update_search_vector(sender, instance, **kwargs):
    # Update the search vector whenever a user is saved
    instance.search_vector = (
        SearchVector('first_name', 'last_name')
    )
    instance.save()
