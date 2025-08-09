from rest_framework import serializers
import random
import uuid
import string

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import authenticate

from main.models import AddictionOption, Conversation, DayPerWeek, EmailVerification, Message, MilestoneProgress, PasswordResetCode, Profile, Addiction, OnboardingData, ProgressQuestion, ProgressAnswer, ProgressResponse, RecoveryMilestone, Report, TargetGoal, Timer, PrivacyPolicy, TermsConditions, SupportContact, AddictionOption, ImproveQuestion, ImproveQuestionOption, MilestoneQuestion, MilestoneOption, JournalEntry, Quote, Suggestion, SuggestionCategory, Notification, MoneySaved
from subscription.models import SubscriptionPlan, UserSubscription

from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="This email is already in use.")]
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def generate_username(self, base):
        username = base
        while User.objects.filter(username=username).exists():
            suffix = ''.join(random.choices(string.digits, k=4))
            username = f"{base}_{suffix}"
        return username

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        email = validated_data['email']
        base_username = email.split('@')[0]
        generated_username = self.generate_username(base_username)

        user = User.objects.create_user(
            username=generated_username,
            email=email,
            password=validated_data['password'],
            is_active=False
        )

        code = str(random.randint(1000, 9999))
        EmailVerification.objects.create(user=user, code=code)

        send_mail(
            'Your Verification Code',
            f'Your verification code is {code}',
            'noreply@example.com',
            [email],
            fail_silently=False
        )

        return user



class EmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is not active")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def create(self, validated_data):
        user = User.objects.get(email=validated_data['email'])
        code = str(random.randint(1000, 9999))

        EmailVerification.objects.create(user=user, code=code)

        send_mail(
            'Password Reset Code',
            f'Your password reset code is {code}',
            'noreply@example.com',
            [user.email],
            fail_silently=False
        )
        return validated_data
    

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def save(self, **kwargs):
        try:
            user = User.objects.get(email=self.validated_data['email'])
            verification = EmailVerification.objects.filter(
                user=user, code=self.validated_data['code']).latest('created_at')

            if verification.is_expired():
                raise serializers.ValidationError("Code has expired.")

            user.set_password(self.validated_data['new_password'])
            user.save()

            # Optionally, delete used codes
            EmailVerification.objects.filter(user=user).delete()

        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            raise serializers.ValidationError("Invalid code or email.")



class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    email = serializers.EmailField(
        source='user.email', 
        read_only=True, 
        validators=[UniqueValidator(queryset=User.objects.all(), message="This email is already in use.")]
    )

    class Meta:
        model = Profile
        fields = ('bio', 'image', 'first_name', 'last_name', 'email')

    def update(self, instance, validated_data):
        # Extract the user data to update first_name, last_name, and email
        user_data = validated_data.pop('user', {})
        
        # Update the profile
        instance.bio = validated_data.get('bio', instance.bio)
        instance.image = validated_data.get('image', instance.image)
        
        # Update user fields if provided
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()  # Save the user fields
        
        instance.save()  # Save the profile
        return instance
    

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'file', 'title', 'uploaded_at']
        read_only_fields = ['id', 'user', 'uploaded_at']

    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        return super().create(validated_data)


class AddictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addiction
        fields = "__all__"
    

class PasswordVerifySerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context['request'].user  # Access the user from the request context
        if not user.check_password(value):  # Check if the password matches
            raise serializers.ValidationError("Invalid password.")
        return value
    

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'duration_days', 'features', 'plan_type']
        orders = ['-price']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer()  # Nested SubscriptionPlan serializer

    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date', 'is_active', 'last_renewed']
    
    def update(self, instance, validated_data):
        plan_data = validated_data.pop('plan', None)
        if plan_data:
            plan = SubscriptionPlan.objects.get(id=plan_data['id'])
            instance.plan = plan
        return super().update(instance, validated_data)
    

class ProgressAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressAnswer
        fields = ['id', 'text']

class ProgressQuestionSerializer(serializers.ModelSerializer):
    answers = ProgressAnswerSerializer(many=True)

    class Meta:
        model = ProgressQuestion
        fields = ['id', 'text', 'answers']


class ProgressResponseSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    question_id = serializers.CharField(source='question.id', read_only=True)
    answer_id = serializers.CharField(source='answer.id', read_only=True)

    class Meta:
        model = ProgressResponse
        fields = ['id', 'user_name', 'question_id', 'answer_id', 'created_at']

    def validate(self, data):
        user = data['user']
        question = data['question']
        
        if ProgressResponse.objects.filter(user=user, question=question).exists():
            raise serializers.ValidationError("You have already answered this question.")
        
        return data
    

class TimerSerializer(serializers.ModelSerializer):
    elapsed_time = serializers.CharField(source='get_elapsed_time', read_only=True)

    class Meta:
        model = Timer
        fields = ['start_time', 'last_restart_time', 'elapsed_time']


class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['name', 'content', 'last_updated']

    def __str__(self):
        return self.name
    

class TermsConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsConditions
        fields = ['name', 'content', 'last_updated']

    def __str__(self):
        return self.name
    

class SupportContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportContact
        fields = ['email', 'phone_primary', 'phone_secondary']

    def __str__(self):
        return f"Support Contact - {self.email}"
    

class AddictionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddictionOption
        fields = ['id', 'name']


'''class OnboardingDataSerializer(serializers.ModelSerializer):
    addiction = AddictionSerializer()
    addiction_option = AddictionOptionSerializer(many=True)

    improvement = serializers.StringRelatedField()  
    milestone = serializers.StringRelatedField() 

    improvement_option = serializers.SerializerMethodField()
    milestone_option = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingData
        fields = "__all__"

    def get_improvement_option(self, obj):
        
        return [{"option": option.id, "text": option.text} for option in obj.improvement_option.all()]

    def get_milestone_option(self, obj):

        return [{"option": option.id, "text": option.text} for option in obj.milestone_option.all()]
'''


class OnboardingDataSerializer(serializers.ModelSerializer):
    addiction_option = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    improvement_option = serializers.SerializerMethodField()
    milestone_option = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingData
        fields = [
            "id",
            "addiction_option",
            "improvement_option",
            "milestone_option",
            "days_per_week",
            "drinks_per_day",
            "trigger_text",
            "completed",
            "user"
        ]

    def get_improvement_option(self, obj):
        return [option.id for option in obj.improvement_option.all()]

    def get_milestone_option(self, obj):
        return [option.id for option in obj.milestone_option.all()]



class DayPerWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingData
        fields = ['days_per_week']


class DrinksPerDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingData
        fields = ['drinks_per_day']


class TriggerTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingData
        fields = ['trigger_text']


class ImproveQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImproveQuestion
        fields = ['text']


class ImproveQuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImproveQuestionOption
        fields = ['question' ,'text']


class MilestoneQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilestoneQuestion
        fields = ['text']


class MilestoneOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilestoneOption
        fields = ['question', 'text']


class MilestoneProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilestoneProgress
        fields = ['milestone_question', 'milestone_option', 'completed_on']



class JournalEntrySerializer(serializers.ModelSerializer):  
    class Meta:
        model = JournalEntry
        fields = ['id', 'title', 'content', 'color', 'created_at', 'updated_at', 'favorite']
        read_only_fields = ['id', 'created_at', 'updated_at']



class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['date', 'text', 'author']


class SuggestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestionCategory
        fields = ['id', 'name', 'logo', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        return super().create(validated_data)


class SuggestionSerializer(serializers.ModelSerializer):
    category = SuggestionCategorySerializer()  # Nested serializer for category details

    class Meta:
        model = Suggestion
        fields = ['id', 'category', 'text', 'video_file', 'view_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'created_at', 'time_ago', 'is_read']

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at) + " ago"


class MoneySavedSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoneySaved
        fields = ['user', 'daily_saving_amount', 'saved_date']


class TargetGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetGoal
        fields = ['user', 'goal_amount', 'target_month']



class RecoveryMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryMilestone
        fields = ['user', 'milestone_name', 'target_date', 'completed']


class MessageSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=[('user', 'User'), ('ai', 'AI')], read_only=True)
    
    timestamp = serializers.DateTimeField(read_only=True)
    
    conversation = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['role', 'content', 'timestamp', 'conversation']
    


class ConversationSerializer(serializers.ModelSerializer):
    # Serialize the related messages using MessageSerializer
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['user_id', 'started_at', 'last_updated', 'messages'] 