from datetime import timedelta, timezone
from django.db import models
import random
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)
   
class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Profile"

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='reports/')
    title = models.CharField(max_length=100, default="Report")
    uploaded_at = models.DateField(auto_now_add=True)


'''class StaticPage(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g. 'privacy', 'terms'
    content = models.TextField()
    last_updated = models.DateField(auto_now=True)'''


'''class SupportContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True)
'''

class Addiction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    addiction_type = models.CharField(max_length=100)
    answer_1 = models.TextField(blank=True)
    answer_2 = models.TextField(blank=True)
    answer_3 = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UsageTracking(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    days_per_week = models.IntegerField(default=0)
    times_per_day = models.IntegerField(default=0)


class AddictionOption(models.Model):
    name = models.CharField(max_length=100, unique=True)

class GoalOption(models.Model):
    text = models.CharField(max_length=200)

class MilestoneOption(models.Model):
    label = models.CharField(max_length=100)

class OnboardingData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    addictions = models.ManyToManyField(AddictionOption, blank=True)
    days_per_week = models.PositiveIntegerField(default=0)
    drinks_per_day = models.PositiveIntegerField(default=0)
    improvement_goals = models.ManyToManyField(GoalOption, blank=True)
    selected_milestone = models.ForeignKey(MilestoneOption, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=False)
