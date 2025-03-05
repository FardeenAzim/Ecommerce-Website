from django.db.models.signals import post_save
from django.dispatch import receiver
from ecommerceapp.models import CustomUser, Profile

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    Profile.objects.get_or_create(user=instance)  # Prevent duplicate profile creation

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
