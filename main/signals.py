from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Addiction, UsageTracking, OnboardingData

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
    
        Profile.objects.create(user=instance)
        Addiction.objects.create(user=instance, addiction_type="None", answer_1="", answer_2="", answer_3="")
        UsageTracking.objects.create(user=instance)
        OnboardingData.objects.create(user=instance)
    else:
        
        if hasattr(instance, 'profile'):
            instance.profile.save()
        if hasattr(instance, 'addiction'):
            instance.addiction.save()
        if hasattr(instance, 'usagetracking'):
            instance.usagetracking.save()
        if hasattr(instance, 'onboardingdata'):
            instance.onboardingdata.save()
