from datetime import timedelta, timezone
from django.db import models
import random
from django.contrib.auth.models import User
from django.utils import timezone
from ckeditor.fields import RichTextField

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


class PrivacyPolicy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    content = RichTextField()
    last_updated = models.DateField(auto_now=True)
    
    def __str__(self):
        return self.name


class TermsConditions(models.Model):
    name = models.CharField(max_length=100, unique=True)
    content = RichTextField()
    last_updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


class SupportContact(models.Model):
    email = models.EmailField()
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Support Contact - {self.email}"
    

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
    
    def __str__(self):
        return f"Usage Tracking for {self.user.email}"


class AddictionOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class GoalOption(models.Model):
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

class MilestoneOption(models.Model):
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label

class OnboardingData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    addictions = models.ManyToManyField(AddictionOption, blank=True)
    days_per_week = models.PositiveIntegerField(default=0)
    drinks_per_day = models.PositiveIntegerField(default=0)
    improvement_goals = models.ManyToManyField(GoalOption, blank=True)
    selected_milestone = models.ForeignKey(MilestoneOption, on_delete=models.SET_NULL, null=True, blank=True)
    triggers_text = models.TextField(blank=True, max_length=500)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Onboarding Data for {self.user.email if self.user else 'Unregistered User'}"


class ProgressQuestion(models.Model):
    text = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text


class ProgressAnswer(models.Model):
    question = models.ForeignKey(ProgressQuestion, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.text} - {self.text}"


class ProgressResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(ProgressQuestion, on_delete=models.CASCADE)
    answer = models.ForeignKey(ProgressAnswer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.email} - {self.question.text} - {self.answer.text}"
    

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='reports/')
    title = models.CharField(max_length=100, default="Report")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Report - {self.title}"
    

class Timer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    last_restart_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Timer for {self.user.username} started at {self.start_time}"

    def get_elapsed_time(self):
        """Return the elapsed time since the last restart."""
        now = timezone.now()
        last_restart = self.last_restart_time or self.start_time
        elapsed_time = now - last_restart
        return str(elapsed_time)

    def restart(self):
        """Restart the timer by updating the last restart time to now."""
        self.last_restart_time = timezone.now()
        self.save()