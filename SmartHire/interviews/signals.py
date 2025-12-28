"""
Django Signals for SmartHire
Handles automatic actions on model events
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, CandidateProfile


@receiver(post_save, sender=User)
def create_candidate_profile(sender, instance, created, **kwargs):
    """Automatically create CandidateProfile when a candidate user is created"""
    if created and instance.role == User.Role.CANDIDATE:
        CandidateProfile.objects.get_or_create(user=instance)


