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
    addiction_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.addiction_type


class AddictionOption(models.Model):
    addiction = models.ForeignKey(Addiction, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name


class DayPerWeek(models.Model):
    addiction = models.ForeignKey(Addiction, on_delete=models.CASCADE)
    days = models.IntegerField(default=0)

    def __str__(self):
        return str(self.days)


class TimesPerDay(models.Model):
    addiction = models.ForeignKey(Addiction, on_delete=models.CASCADE)
    times = models.IntegerField(default=0)

    def __str__(self):
        return str(self.times)


class Trigger(models.Model):
    addiction = models.ForeignKey(Addiction, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)

    def __str__(self):
        return self.text
    

class ImproveQuestion(models.Model):
    text = models.CharField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text
    

class ImproveQuestionOption(models.Model):
    question = models.ForeignKey(ImproveQuestion, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

class MilestoneQuestion(models.Model):
    text = models.CharField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class MilestoneOption(models.Model):
    question = models.ForeignKey(MilestoneQuestion, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question}'s {self.text}"


class OnboardingData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    addiction = models.ForeignKey(Addiction, on_delete=models.CASCADE, blank=True, null=True)  # Make this nullable
    addiction_option = models.ManyToManyField(AddictionOption, blank=True)
    days_per_week = models.PositiveIntegerField(default=0)
    drinks_per_day = models.PositiveIntegerField(default=0)
    trigger_text = models.TextField(blank=True, max_length=500)
    improvement = models.ForeignKey(ImproveQuestion, on_delete=models.CASCADE, blank=True, null=True)
    improvement_option = models.ManyToManyField(ImproveQuestionOption, blank=True, null=True)
    milestone = models.ForeignKey(MilestoneQuestion, on_delete=models.CASCADE, blank=True, null=True)
    milestone_option = models.ManyToManyField(MilestoneOption, blank=True, null=True)
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


class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=20000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorite = models.BooleanField(default=False)

    def __str__(self):
        return f"Journal Entry by {self.user.email} on {self.created_at.strftime('%Y-%m-%d')}"
    

class Quote(models.Model):
    date = models.DateField(auto_now_add=True)
    text = models.TextField()
    author = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.text} — {self.author}"
    

class SuggestionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='suggestion_categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Suggestion(models.Model):
    category = models.ForeignKey(SuggestionCategory, on_delete=models.CASCADE)
    text = models.TextField()
    # video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='suggestion_videos/', blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Suggestion in {self.category.name}: {self.text[:50]}..."
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"
    

class MoneySaved(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    daily_saving_amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_date = models.DateField(auto_now_add=True, null=True)  # Record when the savings were made (date)

    def __str__(self):
        return f"{self.user.username}'s daily saving"

    @classmethod
    def total_savings(cls, user, start_date=None, end_date=None):
        if start_date and end_date:
            return cls.objects.filter(user=user, saved_date__range=[start_date, end_date]).aggregate(total=models.Sum('daily_saving_amount'))['total'] or 0
        return cls.objects.filter(user=user).aggregate(total=models.Sum('daily_saving_amount'))['total'] or 0


class TargetGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    target_month = models.DateField()
    start_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s target for {self.target_month.month}/{self.target_month.year}"
    
    

class RecoveryMilestone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    milestone_name = models.CharField(max_length=100)
    target_date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.milestone_name}"



class MilestoneProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    milestone_question = models.ForeignKey(MilestoneQuestion, on_delete=models.CASCADE)
    milestone_option = models.ForeignKey(MilestoneOption, on_delete=models.CASCADE)
    completed_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Milestone Progress for {self.user.email} on {self.milestone_question.text}"



class Conversation(models.Model):
    """
    Represents a chat session between the user and the AI counselor.
    """
    user_id = models.CharField(max_length=255)  # Store the user's ID or identifier if needed
    started_at = models.DateTimeField(auto_now_add=True)  # Track when the conversation started
    last_updated = models.DateTimeField(auto_now=True)  # Track when the conversation was last updated

    def __str__(self):
        return f"Conversation with {self.user_id} started at {self.started_at}"

class Message(models.Model):
    """
    Represents a single message in the conversation.
    """
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[('user', 'User'), ('ai', 'AI')])  # User or AI
    content = models.TextField()  # Message content
    timestamp = models.DateTimeField(auto_now_add=True)  # Time when the message was sent

    def __str__(self):
        return f"{self.role} at {self.timestamp}: {self.content[:30]}"