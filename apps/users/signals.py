from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import UserProfile


@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid="users.create_user_profile",
)
def create_user_profile(sender, instance, created, raw, using, **kwargs):
    """Create a profile for new users, excluding raw fixture saves."""
    if created:
        UserProfile.objects.get_or_create(user_id=instance.pk)
