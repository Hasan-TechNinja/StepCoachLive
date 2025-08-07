from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import OnboardingData, Profile, Timer
from django.utils import timezone

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
    
        Profile.objects.create(user=instance)
        Timer.objects.create(user=instance, start_time=timezone.now())
        OnboardingData.objects.create(user=instance)
    else:
        
        if hasattr(instance, 'profile'):
            instance.profile.save()
        if hasattr(instance, 'onboardingdata'):
            instance.onboardingdata.save()
        if hasattr(instance, 'timer'):
            instance.timer.save()