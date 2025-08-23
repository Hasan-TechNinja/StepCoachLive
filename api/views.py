import random
import stripe
from tokenize import TokenError
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone 
from datetime import timedelta, date
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import datetime
import openai
from rest_framework.exceptions import NotFound
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password

from api.ai import AICounselor
from main.models import Conversation, DayPerWeek, EmailVerification, Message, MilestoneProgress, MoneySaved, PasswordResetCode, Profile, Addiction, OnboardingData, ProgressQuestion, ProgressAnswer, ProgressResponse, RecoveryMilestone, Report, TargetGoal, Timer, PrivacyPolicy, TermsConditions, SupportContact, AddictionOption, ImproveQuestion, ImproveQuestionOption, MilestoneQuestion, MilestoneOption, JournalEntry, Quote, Suggestion, SuggestionCategory, Notification
from api.serializers import ConversationSerializer, DayPerWeekSerializer, DrinksPerDaySerializer, MessageSerializer, MilestoneProgressSerializer, MoneySavedSerializer, OnboardingDataSerializer, PasswordVerifySerializer, RecoveryMilestoneSerializer, RegistrationSerializer, EmailTokenObtainPairSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ProfileSerializer, AddictionSerializer, SubscriptionPlanSerializer, TargetGoalSerializer, TimerSerializer, TriggerTextSerializer, UserSubscriptionSerializer, ProgressQuestionSerializer, ProgressAnswerSerializer, ProgressResponseSerializer, ProgressQuestionSerializer, ReportSerializer, PrivacyPolicySerializer, TermsConditionsSerializer, SupportContactSerializer, AddictionOptionSerializer, ImproveQuestionSerializer, ImproveQuestionOptionSerializer, MilestoneQuestionSerializer, MilestoneOptionSerializer, JournalEntrySerializer, QuoteSerializer, SuggestionSerializer, SuggestionCategorySerializer, NotificationSerializer
from subscription.models import SubscriptionPlan, UserSubscription

from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


# Create your views here.
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user:
            # If the user exists but is not active, resend the verification code
            if not existing_user.is_active:
                # Delete any previous OTP code (if exists)
                EmailVerification.objects.filter(user=existing_user).delete()

                # Generate a new verification code
                code = str(random.randint(1000, 9999))
                EmailVerification.objects.create(user=existing_user, code=code)

                send_mail(
                    subject='Your New Verification Code',
                    message=(
                        f"Hello {email},\n\n"
                        "Thank you for registering with us.\n"
                        f"Your verification code is: {code}\n\n"
                        "Please use this code to verify your account.\n"
                        "If you did not request this, please ignore this email.\n\n"
                        "Best regards,\n"
                        "The 1 Step Coach Live Team"
                    ),
                    from_email='noreply@example.com',
                    recipient_list=[email],
                    fail_silently=False
                )

                return Response({"message": "A new verification code has been sent to your email."}, status=status.HTTP_200_OK)
            
            # If the user is active, inform that email is already in use
            return Response({"error": "This email is already in use by an active account."}, status=status.HTTP_400_BAD_REQUEST)
        
        # If the email does not exist, proceed with the registration process
        serializer = RegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()

            # Generate refresh token and access token using Simple JWT
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Send a notification about successful registration
            Notification.objects.create(
                user=user,
                title="Registration Successful",
                message="Welcome to One StepCoach! Your account has been created successfully.",
            )

            return Response({'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class ResendVerificationCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response({"message": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)

            # Delete old code if exists
            EmailVerification.objects.filter(user=user).delete()

            # Generate new code
            code = str(random.randint(1000, 9999))
            EmailVerification.objects.create(user=user, code=code)

            send_mail(
                    subject='Your New Verification Code',
                    message=(
                        f"Hello {email},\n\n"
                        "Thank you for registering with us.\n"
                        f"Your verification code is: {code}\n\n"
                        "Please use this code to verify your account.\n"
                        "If you did not request this, please ignore this email.\n\n"
                        "Best regards,\n"
                        "The 1 Step Coach Live Team"
                    ),
                    from_email='noreply@example.com',
                    recipient_list=[email],
                    fail_silently=False
                )

            return Response({"message": "A new verification code has been sent to your email."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

  

class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')
        email = request.data.get('email')

        if not code or not email:
            return Response({"error": "Code and email are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)

            if verification.code == code:
                if verification.is_expired():
                    return Response({"error": "Verification code has expired."}, status=status.HTTP_400_BAD_REQUEST)

                user.is_active = True
                user.save()

                verification.delete()

                login(request, user)

                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                return Response({
                    'message': 'Email verified successfully and user logged in.',
                    'access': str(access_token),
                    'refresh': str(refresh)
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except EmailVerification.DoesNotExist:
            return Response({"error": "No verification record found for this user."}, status=status.HTTP_404_NOT_FOUND)
      

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if refresh_token is None:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create token object from the refresh token string
            token = RefreshToken(refresh_token)

            # Blacklist the token
            token.blacklist()

            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)

        except InvalidToken:
            return Response({"detail": "The token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class EmailLoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            if not user.is_active:
                return Response({"error": "User is not active."}, status=status.HTTP_400_BAD_REQUEST)

            PasswordResetCode.objects.filter(user=user).delete()

            code = str(random.randint(1000, 9999))

            PasswordResetCode.objects.create(user=user, code=code)

            if user.first_name and user.last_name:
                name = f"{user.first_name} {user.last_name}"
            elif user.email:
                name = user.email
            else:
                name = user.username

            send_mail(
                subject='Password Reset Request',
                message=(
                    f"Hello, {name}\n"
                    "We received a request to reset your account password.\n"
                    f"Your password reset code is: "
                    f"{code}\n\n"
                    "If you did not request this, please ignore this email.\n"
                    # "For security, this code will expire in 10 minutes.\n\n"
                    "Best regards,\n"
                    "The 1 Step Coach Live Team"
                ),
                from_email='noreply@example.com',
                recipient_list=[email],
                fail_silently=False
            )

            return Response({"message": "A password reset code has been sent to your email."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)

                password_reset = PasswordResetCode.objects.filter(user=user, code=code).first()

                if not password_reset:
                    return Response({"error": "Invalid or expired reset code."}, status=status.HTTP_400_BAD_REQUEST)

                user.password = make_password(new_password)
                user.save()

                password_reset.delete()

                return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET: Retrieve the user's profile
    def get(self, request):
        user = request.user
        profile = ProfileSerializer(user.profile).data
        return Response(profile, status=status.HTTP_200_OK)

    # PUT: Update the user's profile
    def put(self, request):
        user = request.user
        serializer = ProfileSerializer(user.profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            Notification.objects.create(
                user = user,
                title = "Profile Updated",
                message = "Your profile has been updated successfully." 
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Delete the user's account after password verification
    def delete(self, request):
        user = request.user
        password_serializer = PasswordVerifySerializer(data=request.data, context={'request': request})  # Pass request to context

        if password_serializer.is_valid():
            # Delete related models using direct relationships (no *_set needed for OneToOneField)
            user.profile.delete()
            user.addiction_set.all().delete()  # Deletes all Addiction entries for the user
            if hasattr(user, 'onboardingdata'):  # Directly access onboardingdata (since it's OneToOneField)
                user.onboardingdata.delete()  # Deletes OnboardingData entry for the user

            # Finally, delete the user account from the User table
            user.delete()

            return Response({'detail': 'Account deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

        return Response(password_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddictionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        addiction = Addiction.objects.all()
        serializer = AddictionSerializer(addiction, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddictionDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            addiction = Addiction.objects.get(id=pk)
            addiction_options = AddictionOption.objects.filter(addiction=addiction)

            # Serialize AddictionOptions related to the addiction
            addiction_options_serializer = AddictionOptionSerializer(addiction_options, many=True)

            # Return Addiction type and its options
            response_data = {
                'addiction_id': addiction.id,
                'addiction_type': addiction.addiction_type,
                'addiction_options': addiction_options_serializer.data
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Addiction.DoesNotExist:
            return Response({"detail": "Addiction not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        user = request.user

        # Retrieve the Addiction object or create if it doesn't exist
        try:
            addiction = Addiction.objects.get(id=pk)
        except Addiction.DoesNotExist:
            return Response({"detail": "Addiction not found"}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve or create OnboardingData for the authenticated user
        onboarding, created = OnboardingData.objects.get_or_create(user=user)

        # Set the addiction field in OnboardingData
        onboarding.addiction = addiction

        # Get the addiction options from the request data (IDs of the addiction options)
        addiction_option_ids = request.data.get('addiction_option', [])
        
        # Check if more than one addiction option is provided
        if len(addiction_option_ids) > 1:
            return Response({"detail": "You can only select one addiction option at a time."}, status=status.HTTP_400_BAD_REQUEST)

        if addiction_option_ids:
            # Fetch AddictionOption objects based on the provided ID
            addiction_options = AddictionOption.objects.filter(id__in=addiction_option_ids)
            
            # Ensure the provided option exists
            if addiction_options.count() != len(addiction_option_ids):
                return Response({"detail": "One or more addiction options are invalid."}, status=status.HTTP_400_BAD_REQUEST)

            # Set the addiction option in OnboardingData (this will replace any existing option)
            onboarding.addiction_option.set(addiction_options)

        # Set additional fields in OnboardingData if provided
        onboarding.days_per_week = request.data.get('days_per_week', 0)
        onboarding.drinks_per_day = request.data.get('drinks_per_day', 0)
        onboarding.trigger_text = request.data.get('trigger_text', '')

        # Handle Improvement and Milestone related fields if provided
        if 'improvement' in request.data:
            try:
                onboarding.improvement = ImproveQuestion.objects.get(id=request.data['improvement'])
            except ImproveQuestion.DoesNotExist:
                return Response({"detail": "Improvement question not found."}, status=status.HTTP_404_NOT_FOUND)

        if 'milestone' in request.data:
            try:
                onboarding.milestone = MilestoneQuestion.objects.get(id=request.data['milestone'])
            except MilestoneQuestion.DoesNotExist:
                return Response({"detail": "Milestone question not found."}, status=status.HTTP_404_NOT_FOUND)

        # Handle Improvement and Milestone Options (IDs of the options)
        if 'improvement_option' in request.data:
            improvement_option_ids = request.data['improvement_option']
            if improvement_option_ids:
                # Fetch ImproveQuestionOption objects based on the IDs provided
                improvement_options = ImproveQuestionOption.objects.filter(id__in=improvement_option_ids)
                # Add options to existing improvement options (without replacing)
                onboarding.improvement_option.add(*improvement_options)

        if 'milestone_option' in request.data:
            milestone_option_ids = request.data['milestone_option']
            if milestone_option_ids:
                milestone_options = MilestoneOption.objects.filter(id__in=milestone_option_ids)
                onboarding.milestone_option.set(milestone_options)

        # Save OnboardingData
        onboarding.save()

        # Prepare the response
        response_data = {
            "detail": "Onboarding data successfully saved.",
            "onboarding_data": {
                "addiction": {
                    "id": onboarding.addiction.id,
                    "addiction_type": onboarding.addiction.addiction_type
                },
                "addiction_option": [
                    {"id": option.id, "name": option.name} for option in onboarding.addiction_option.all()
                ],
                "days_per_week": onboarding.days_per_week,
                "drinks_per_day": onboarding.drinks_per_day,
                "trigger_text": onboarding.trigger_text,
                "improvement": {
                    "id": onboarding.improvement.id if onboarding.improvement else None,
                    "question": onboarding.improvement.text if onboarding.improvement else None
                },
                "milestone": {
                    "id": onboarding.milestone.id if onboarding.milestone else None,
                    "question": onboarding.milestone.text if onboarding.milestone else None
                },
                "improvement_option": [
                    {"id": option.id, "text": option.text} for option in onboarding.improvement_option.all()
                ],
                "milestone_option": [
                    {"id": option.id, "text": option.text} for option in onboarding.milestone_option.all()
                ],
                "completed": onboarding.completed
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)
    



class DrinksRateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Attempt to get the OnboardingData, otherwise create it if missing
        onboarding_data, created = OnboardingData.objects.get_or_create(user=user)
        
        # If onboarding data was created, you may choose to return a different status or response
        if created:
            return Response({"detail": "Onboarding data created with default values."}, status=status.HTTP_201_CREATED)

        day_serializer = DayPerWeekSerializer(onboarding_data)
        drink_serializer = DrinksPerDaySerializer(onboarding_data)

        return Response({
            'days_per_week': day_serializer.data,
            'drinks_per_day': drink_serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        
        # Attempt to get the OnboardingData, otherwise create it if missing
        onboarding_data, created = OnboardingData.objects.get_or_create(user=user)

        # Handle the case when the user is posting data
        drinks_per_day = request.data.get('drinks_per_day')
        days_per_week = request.data.get('days_per_week')

        if drinks_per_day is not None:
            onboarding_data.drinks_per_day = drinks_per_day
        
        if days_per_week is not None:
            onboarding_data.days_per_week = days_per_week

        onboarding_data.save()

        day_serializer = DayPerWeekSerializer(onboarding_data)
        drink_serializer = DrinksPerDaySerializer(onboarding_data)

        return Response({
            'days_per_week': day_serializer.data,
            'drinks_per_day': drink_serializer.data
        }, status=status.HTTP_200_OK)


class TriggerTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            # Fetch the OnboardingData for the user
            onboarding_data = OnboardingData.objects.get(user=user)
        except OnboardingData.DoesNotExist:
            return Response({"detail": "Onboarding data not found"}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the `trigger_text` field
        trigger_serializer = TriggerTextSerializer(onboarding_data)

        # Return the serialized data
        return Response(trigger_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        
        try:
            # Fetch the OnboardingData for the user
            onboarding_data = OnboardingData.objects.get(user=user)
        except OnboardingData.DoesNotExist:
            return Response({"detail": "Onboarding data not found"}, status=status.HTTP_404_NOT_FOUND)

        # Handle the `trigger_text` and `created_at` fields
        trigger_text = request.data.get('trigger_text')
        created_at = request.data.get('created_at')

        if trigger_text is not None and created_at is not None:
            # Update the `trigger_text` field
            onboarding_data.trigger_text = trigger_text

            # Set the `completed` field to True when `trigger_text` is updated
            onboarding_data.completed = True

            # Save the `created_at` field with the provided text
            onboarding_data.created_at = created_at  # The provided 'created_at' text

            # Save the OnboardingData instance
            onboarding_data.save()

            # Create a notification for the user about onboarding completion
            Notification.objects.create(
                user=user,
                title="Onboarding Completed",
                message="You have successfully completed the onboarding process by providing your data.",
            )

            # Serialize and return the updated `trigger_text` and `created_at`
            trigger_serializer = TriggerTextSerializer(onboarding_data)
            return Response(trigger_serializer.data, status=status.HTTP_200_OK)
        else:
            # If trigger_text or created_at is not provided, return a bad request response
            return Response({"detail": "'trigger_text' and 'created_at' fields are required"}, status=status.HTTP_400_BAD_REQUEST)




class ImproveQuestionAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the first question only for simplicity
        question = ImproveQuestion.objects.first()
        if not question:
            return Response({"detail": "No improvement question found."}, status=status.HTTP_404_NOT_FOUND)

        options = ImproveQuestionOption.objects.filter(question=question)
        formatted_options = [
            {'option': option.id, 'text': option.text}
            for option in options
        ]

        return Response({
            'question': question.text,
            'options': formatted_options
        }, status=status.HTTP_200_OK)


    def post(self, request):
        user = request.user
        option_ids = request.data.get("improvement_option", [])

        if isinstance(option_ids, str):
            option_ids = option_ids.split(",")
            option_ids = [int(i.strip()) for i in option_ids]

        if not isinstance(option_ids, list) or not all(isinstance(i, int) for i in option_ids):
            return Response({"detail": "Improvement option IDs must be a list of integers."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch options from DB
        selected_options = ImproveQuestionOption.objects.filter(id__in=option_ids)

        if selected_options.count() != len(option_ids):
            return Response({"detail": "One or more improvement options are invalid."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create onboarding data
        onboarding, _ = OnboardingData.objects.get_or_create(user=user)

        # All selected options should be from the same question
        question = selected_options.first().question if selected_options else None

        if not question:
            return Response({"detail": "No associated improvement question found."}, status=status.HTTP_400_BAD_REQUEST)

        # Save improvement and selected options
        onboarding.improvement = question
        onboarding.improvement_option.set(selected_options)
        onboarding.save()

        # Format response
        response_data = {
            "improvement": question.text,
            "improvement_option": [
                {"option": opt.id, "text": opt.text}
                for opt in selected_options
            ]
        }

        return Response(response_data, status=status.HTTP_200_OK)




class MilestoneQuestionAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        question = MilestoneQuestion.objects.first()
        if not question:
            return Response({"detail": "No milestone question found."}, status=status.HTTP_404_NOT_FOUND)

        options = MilestoneOption.objects.filter(question=question)
        
        formatted_options = [
            {
                'option': option.id,
                'text': option.text
            } for option in options
        ]
        
        response_data = {
            'question': question.text,
            'options': formatted_options
        }

        return Response(response_data, status=status.HTTP_200_OK)



    def post(self, request):
        user = request.user

        milestone_options_data = request.data.get('milestone_options', [])

        if not milestone_options_data:
            return Response({"detail": "Milestone options are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            milestone_options = MilestoneOption.objects.filter(id__in=milestone_options_data)
        except MilestoneOption.DoesNotExist:
            return Response({"detail": "One or more milestone options are invalid."}, status=status.HTTP_400_BAD_REQUEST)

        milestone_question = milestone_options.first().question

        if len(milestone_options) > 1:
            return Response({"detail": "You can select a maximum of 1 milestone options."}, status=status.HTTP_400_BAD_REQUEST)

        onboarding_data, created = OnboardingData.objects.get_or_create(user=user)

        onboarding_data.milestone = milestone_question
        onboarding_data.milestone_option.set(milestone_options)
        onboarding_data.save()

        return Response({"detail": "Milestone data saved successfully."}, status=status.HTTP_201_CREATED)


        

class OnboardingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        onboarding = OnboardingData.objects.get(user = request.user)
        serializer = OnboardingDataSerializer(onboarding)
        return Response(serializer.data)
        



class AddictionSelectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve a list of all addictions."""
        addictions = AddictionOption.objects.all()
        serializer = AddictionOptionSerializer(addictions, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Save the selected addictions."""
        try:
            onboarding_data, created = OnboardingData.objects.get_or_create(user=request.user)
            addiction_ids = request.data.get("addictions", [])
            addictions = AddictionOption.objects.filter(id__in=addiction_ids)
            onboarding_data.addictions.set(addictions)
            onboarding_data.save()
            return Response({"detail": "Addictions updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class DrinkingHabitsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Update the drinking habits of the user."""
        try:
            onboarding_data = OnboardingData.objects.get(user=request.user)
            onboarding_data.days_per_week = request.data.get("days_per_week", 0)
            onboarding_data.drinks_per_day = request.data.get("drinks_per_day", 0)
            onboarding_data.save()
            return Response({"detail": "Drinking habits updated."}, status=status.HTTP_200_OK)
        except OnboardingData.DoesNotExist:
            return Response({"detail": "Onboarding data not found."}, status=status.HTTP_404_NOT_FOUND)



class TriggersTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Save the triggers text."""
        try:
            # Check if onboarding data exists for the authenticated user
            onboarding_data, created = OnboardingData.objects.get_or_create(user=request.user)
            
            # Update triggers text and mark the onboarding process as completed
            onboarding_data.triggers_text = request.data.get("triggers_text", "")
            onboarding_data.completed = True  # Mark the onboarding as complete
            
            # Save the changes
            onboarding_data.save()

            return Response({"detail": "Triggers updated."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class ReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        reports = Report.objects.filter(user=request.user)
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):

        serializer = ReportSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()

            Notification.objects.create(
                user=request.user,
                title="Report Submitted",
                message="Your report has been submitted successfully.",
            )   
        
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class PrivacyPolicyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the privacy policy."""
        try:
            policy = PrivacyPolicy.objects.first()
            serializer = PrivacyPolicySerializer(policy)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PrivacyPolicy.DoesNotExist:
            return Response({"detail": "Privacy policy not found."}, status=status.HTTP_404_NOT_FOUND)
        

class TermsConditionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the terms and conditions."""
        try:
            terms = TermsConditions.objects.first()
            serializer = TermsConditionsSerializer(terms)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TermsConditions.DoesNotExist:
            return Response({"detail": "Terms and conditions not found."}, status=status.HTTP_404_NOT_FOUND)
        


class SupportContactView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the support contact information."""
        try:
            contact = SupportContact.objects.first()
            serializer = SupportContactSerializer(contact)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SupportContact.DoesNotExist:
            return Response({"detail": "Support contact not found."}, status=status.HTTP_404_NOT_FOUND)



# --------------------------------------- Subscription --------------------------------------------------------
   

class SubscriptionPlanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve all subscription plans."""
        plans = SubscriptionPlan.objects.all().order_by('price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new subscription plan (admin only)."""
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission to create subscription plans."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save()
            return Response(SubscriptionPlanSerializer(plan).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Set Stripe API Key
stripe.api_key = settings.STRIPE_SECRET_KEY

class UserSubscriptionViewSet(viewsets.GenericViewSet):

    '''Subscription add demo
    
    ["Basic AI Chat", "Daily Check-ins", "Milestone Tracking", "Voice Responses", "Advanced Analytics", "Personalized Content", "Priority Support"]
'''
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter to get the subscription for the authenticated user."""
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retrieve the current subscription for the authenticated user."""
        try:
            user_subscription = self.get_queryset().get()  # Should be OneToOne, so get() works
            serializer = self.get_serializer(user_subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserSubscription.DoesNotExist:
            return Response({"message": "No active subscription found for this user."},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def current_active(self, request):
        """Check if the user has an active subscription."""
        user_subscription = self.get_queryset().filter(is_active=True).first()
        if user_subscription:
            serializer = self.get_serializer(user_subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "No active subscription found for this user."},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Create a Stripe checkout session for the user to subscribe to a plan."""
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({"error": "Plan ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Subscription plan not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        try:
            # Try to fetch user's current subscription (if any)
            user_subscription = UserSubscription.objects.get(user=user)

            if user_subscription.is_active:
                if user_subscription.plan.id == plan.id:
                    return Response(
                        {"error": "You already have an active subscription to this plan."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Upgrade/downgrade: deactivate and update to new plan
                    user_subscription.plan = plan
                    user_subscription.is_active = False
                    user_subscription.start_date = timezone.now()
                    user_subscription.save()

        except UserSubscription.DoesNotExist:
            # No subscription found — create a new one
            user_subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                is_active=False,
                start_date=timezone.now(),
            )

        # Create Stripe Checkout Session
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,
                line_items=[{
                    'price_data': {
                        'currency': 'gbp',
                        'product_data': {
                            'name': plan.name,
                        },
                        'unit_amount': int(plan.price * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(f'/payments/success/{user_subscription.id}/'),
                cancel_url=request.build_absolute_uri('/payments/cancel/'),
                metadata={
                    'user_id': user.id,
                    'plan_id': plan.id,
                    'subscription_id': user_subscription.id
                }
            )
            return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel the active subscription for the authenticated user."""
        try:
            user_subscription = self.get_queryset().get(is_active=True)
            user_subscription.is_active = False
            user_subscription.save()
            serializer = self.get_serializer(user_subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserSubscription.DoesNotExist:
            return Response({"message": "No active subscription found to cancel."},
                             status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def renew(self, request):
        """Renew the user's subscription."""
        try:
            user_subscription = self.get_queryset().get(is_active=True)
            # Renew logic: Extend the end_date by the plan's duration
            if user_subscription.plan.duration_days:
                user_subscription.end_date += timedelta(days=user_subscription.plan.duration_days)
                user_subscription.last_renewed = timezone.now()
                user_subscription.save()
                serializer = self.get_serializer(user_subscription)
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response({"message": "This plan does not support renewal."},
                             status=status.HTTP_400_BAD_REQUEST)
        except UserSubscription.DoesNotExist:
            return Response({"message": "No active subscription found to renew."},
                             status=status.HTTP_404_NOT_FOUND)
        
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeWebhookView(APIView):

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        # Retrieve the request's body as a string
        payload = request.body.decode('utf-8')
        sig_header = request.headers.get('Stripe-Signature')

        event = None

        try:
            # Verify the webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return JsonResponse({'message': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return JsonResponse({'message': 'Invalid signature'}, status=400)

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            # Get the subscription ID and user ID from the metadata
            subscription_id = session['metadata']['subscription_id']
            user_id = session['metadata']['user_id']

            # Fetch the subscription object
            user_subscription = get_object_or_404(UserSubscription, id=subscription_id, user_id=user_id)

            # Update subscription status to active
            user_subscription.is_active = True
            user_subscription.save()

            # Optionally: You can set the end date, last renewed, etc.
            # user_subscription.end_date = calculate_end_date_based_on_plan(user_subscription.plan)
            # user_subscription.last_renewed = timezone.now()
            # user_subscription.save()

            # Respond with a success message
            return JsonResponse({'status': 'success'}, status=200)

        # Unexpected event type
        return JsonResponse({'message': 'Event type not supported'}, status=400)
    


class SuccessView(APIView):
    """
    Handle successful Stripe payments. Activate the subscription.
    """

    def get(self, request, subscription_id):
        try:
            subscription = UserSubscription.objects.get(id=subscription_id)

            # Activate the subscription
            subscription.is_active = True
            subscription.start_date = timezone.now()
            subscription.save()

            Notification.objects.create(
                user=subscription.user,
                title="Subscription Activated",
                message=f"Your subscription to {subscription.plan.name} has been activated successfully.",
            )

            return Response({
                "message": "Subscription activated successfully!",
                "subscription_id": subscription.id,
                "plan": subscription.plan.name,
                "user": subscription.user.email,
                "active": subscription.is_active,
                "start_date": subscription.start_date,
            }, status=status.HTTP_200_OK)

        except UserSubscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)
        


class CancelPaymentView(APIView):
    """
    Handle cancellation of Stripe payments and deactivate the subscription.
    """

    def post(self, request, subscription_id):
        try:
            subscription = UserSubscription.objects.get(id=subscription_id)

            # Deactivate the subscription
            subscription.is_active = False
            subscription.end_date = timezone.now()  # Set end date as now
            subscription.save()

            return Response({
                "message": "Subscription canceled successfully.",
                "subscription_id": subscription.id,
                "plan": subscription.plan.name,
                "user": subscription.user.email,
                "active": subscription.is_active,
                "end_date": subscription.end_date,
            }, status=status.HTTP_200_OK)

        except UserSubscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
    
# --------------------------------------- End of Subscription --------------------------------------------------------


class UserProgressTest(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve all active progress questions with their answer options."""
        questions = ProgressQuestion.objects.filter(is_active=True).prefetch_related('answers')
        serializer = ProgressQuestionSerializer(questions, many=True)
        return Response({'questions': serializer.data}, status=status.HTTP_200_OK)
    

class SubmitProgressResponses(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        responses = request.data.get('responses', [])

        if not responses:
            return Response({"detail": "No responses provided."}, status=status.HTTP_400_BAD_REQUEST)

        saved = []
        errors = []

        for entry in responses:
            question_id = entry.get('question')
            answer_id = entry.get('answer')

            try:
                question = ProgressQuestion.objects.get(id=question_id)
                answer = ProgressAnswer.objects.get(id=answer_id, question=question)
            except ProgressQuestion.DoesNotExist:
                errors.append({"question": question_id, "error": "Question not found"})
                continue
            except ProgressAnswer.DoesNotExist:
                errors.append({"answer": answer_id, "error": "Answer not valid for question"})
                continue

            # Check if user already answered
            if ProgressResponse.objects.filter(user=request.user, question=question).exists():
                errors.append({"question": question_id, "error": "Already answered"})
                continue

            response_obj = ProgressResponse(user=request.user, question=question, answer=answer)
            response_obj.save()
            saved.append({"question": question_id, "answer": answer_id})

        # 🔔 Create exactly one notification for this submit, if anything was saved
        if saved:
            Notification.objects.create(
                user=request.user,
                title="Progress responses submitted",
                message=f"You submitted {len(saved)} answer(s) successfully.",
                is_read=False
            )

        return Response(
            {"saved": saved, "errors": errors},
            status=status.HTTP_201_CREATED if saved else status.HTTP_400_BAD_REQUEST
        )


    

class ProgressResultView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the user's progress responses."""
        responses = ProgressResponse.objects.filter(user=request.user).select_related('question', 'answer')
        serializer = ProgressResponseSerializer(responses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

class TimerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            timer = Timer.objects.get(user=request.user)
            
            serializer = TimerSerializer(timer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Timer.DoesNotExist:
            return Response({"error": "Timer not found for this user"}, status=status.HTTP_404_NOT_FOUND)
    
    
class RestartTimerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            timer = Timer.objects.get(user=request.user)
            
            timer.restart()
            Notification.objects.create(
                user=request.user,
                title="Timer Restarted",
                message="Your timer has been restarted successfully.",
            )
            return Response({"message": "Timer restarted", "elapsed_time": timer.get_elapsed_time()}, status=status.HTTP_200_OK)
        except Timer.DoesNotExist:
            return Response({"error": "Timer not found for this user"}, status=status.HTTP_404_NOT_FOUND)
        


class JournalEntryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve all journal entries for the authenticated user."""
        entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
        serializer = JournalEntrySerializer(entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new journal entry."""
        serializer = JournalEntrySerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class FavoriteJournalEntriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve all favorite journal entries for the authenticated user."""
        # Filter favorite entries for the authenticated user and order by creation date
        entries = JournalEntry.objects.filter(user=request.user, favorite=True).order_by('-created_at')
        
        # Serialize the entries
        serializer = JournalEntrySerializer(entries, many=True)
        
        # Return the serialized data with HTTP 200 OK status
        return Response(serializer.data, status=status.HTTP_200_OK)


class JournalEntryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Retrieve a specific journal entry by ID."""
        try:
            entry = JournalEntry.objects.get(id=pk, user=request.user)
            serializer = JournalEntrySerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except JournalEntry.DoesNotExist:
            return Response({"detail": "Journal entry not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        """Update a specific journal entry."""
        try:
            entry = JournalEntry.objects.get(id=pk, user=request.user)
            serializer = JournalEntrySerializer(entry, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except JournalEntry.DoesNotExist:
            return Response({"detail": "Journal entry not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        """Delete a specific journal entry."""
        try:
            entry = JournalEntry.objects.get(id=pk, user=request.user)
            entry.delete()
            return Response({"detail": "Journal entry deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except JournalEntry.DoesNotExist:
            return Response({"detail": "Journal entry not found."}, status=status.HTTP_404_NOT_FOUND)
        


class MotivationalQuoteAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Instantiate the AICounselor class
        counselor = AICounselor()

        # Get a motivational quote from the AI class
        quote = counselor.get_motivational_quote()

        # Return the quote as a JSON response using DRF's Response class
        return Response({'motivational_quote': quote})
    
    

class SuggestionLiarView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retrieve all suggestions."""
        category = SuggestionCategory.objects.all().order_by('-created_at')  # You can add pagination here
        serializer = SuggestionCategorySerializer(category, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuggestionDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        category = SuggestionCategory.objects.get(id = pk)
        suggestions = Suggestion.objects.filter(category=category).order_by('-created_at')  # You can add pagination here
        serializer = SuggestionSerializer(suggestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 
    

class SuggestionVideoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, id):
        try:
            suggestion = Suggestion.objects.get(id=id, category__id=pk)  # Correct model and query
        except Suggestion.DoesNotExist:
            raise NotFound("Suggestion not found")
        
        # Increment view count for the suggestion
        suggestion.view_count += 1
        suggestion.save()

        # Serialize the suggestion and return it
        serializer = SuggestionSerializer(suggestion)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class PopularSuggestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the most popular suggestion."""
        try:
            popular_suggestion = Suggestion.objects.order_by('-view_count')[:10]
            if not popular_suggestion:
                return Response({"detail": "No suggestions available."}, status=status.HTTP_404_NOT_FOUND)

            serializer = SuggestionSerializer(popular_suggestion, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class RecentSuggestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the most recent suggestion."""
        try:
            recent_suggestion = Suggestion.objects.order_by('-created_at')[:10]
            if not recent_suggestion:
                return Response({"detail": "No suggestions available."}, status=status.HTTP_404_NOT_FOUND)

            serializer = SuggestionSerializer(recent_suggestion, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    


class MarkNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "All notifications marked as read."})


'''class TargetGoalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user  # Automatically fetch the logged-in user
        
        data = request.data.copy()
        # Set the target month to the current month or provided by the user
        if not data.get('target_month'):
            data['target_month'] = date.today().replace(day=1)

        # Automatically add the logged-in user to the data
        data['user'] = user.id
        
        serializer = TargetGoalSerializer(data=data)

        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    '''

def first_of_month(d: date) -> date:
    return d.replace(day=1)

class TargetGoalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Get or default target_month
        raw_tm = request.data.get("target_month")
        if raw_tm:
            # Accept "YYYY-MM-DD" or "YYYY-MM"
            try:
                if len(raw_tm) == 7:  # "YYYY-MM"
                    tm = datetime.strptime(raw_tm, "%Y-%m").date()
                else:
                    tm = datetime.strptime(raw_tm, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"target_month": ["Use YYYY-MM or YYYY-MM-DD."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            tm = date.today()

        tm = first_of_month(tm)

        # Upsert: update if exists for (user, target_month), else create
        payload = {
            "goal_amount": request.data.get("goal_amount"),
        }
        # Validate with serializer first (without committing)
        ser = TargetGoalSerializer(data={"goal_amount": payload["goal_amount"], "target_month": tm})
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        obj, created = TargetGoal.objects.update_or_create(
            user=user,
            target_month=tm,
            defaults={"goal_amount": ser.validated_data["goal_amount"]},
        )

        out = TargetGoalSerializer(obj)
        return Response(out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    

class MoneySavedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        # Calculate today's savings
        today_savings = MoneySaved.total_savings(user, start_date=today, end_date=today)
        
        # Calculate weekly savings (from the beginning of the current week)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_savings = MoneySaved.total_savings(user, start_date=week_start, end_date=week_end)

        # Calculate monthly savings
        month_start = today.replace(day=1)
        month_end = today.replace(day=28) + timedelta(days=4)
        monthly_savings = MoneySaved.total_savings(user, start_date=month_start, end_date=month_end)

        # Calculate target goal for the current month
        target_goal = TargetGoal.objects.filter(user=user, target_month__month=today.month).first()
        target_goal_amount = target_goal.goal_amount if target_goal else 0
        percentage_goal = (monthly_savings / target_goal_amount) * 100 if target_goal_amount else 0

        # Show the data
        savings_data = {
            'today_savings': today_savings,
            'weekly_savings': weekly_savings,
            'monthly_savings': monthly_savings,
            'total_savings': MoneySaved.total_savings(user),
            'percentage_goal': percentage_goal,
            'target_goal_amount': target_goal_amount,
        }

        return Response(savings_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user  # Automatically fetch the logged-in user
        
        # Remove user field from the incoming data and set the user from the request
        data = request.data.copy()  # Make a copy of the incoming data to modify it
        data['user'] = user.id  # Automatically set the user ID

        serializer = MoneySavedSerializer(data=data)

        if serializer.is_valid():
            # Save the data with the authenticated user
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    

class RecoveryMilestoneView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        milestones = RecoveryMilestone.objects.filter(user=user)

        if not milestones:
            return Response({"detail": "No recovery milestones found"}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data and add the username manually
        serialized_data = RecoveryMilestoneSerializer(milestones, many=True).data

        # Add the username field to the serialized data
        for item in serialized_data:
            item["username"] = user.username  # Add the username to each item in the list

        return Response(serialized_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        serializer = RecoveryMilestoneSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ViewMilestonesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Retrieve all milestones progress related to the user
        milestones_progress = MilestoneProgress.objects.filter(user=user)

        if not milestones_progress:
            return Response({"detail": "No milestones found for this user."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the milestones progress data
        serialized_data = MilestoneProgressSerializer(milestones_progress, many=True).data

        # Add username to the data for clarity
        for item in serialized_data:
            item["username"] = user.username

        return Response(serialized_data, status=status.HTTP_200_OK)
    

class CompleteMilestoneAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        milestone_question_id = request.data.get('milestone_question')
        milestone_option_id = request.data.get('milestone_option')

        try:
            milestone_question = MilestoneQuestion.objects.get(id=milestone_question_id)
            milestone_option = MilestoneOption.objects.get(id=milestone_option_id)

            # Save the progress of the user
            milestone_progress = MilestoneProgress.objects.create(
                user=user,
                milestone_question=milestone_question,
                milestone_option=milestone_option
            )

            Notification.objects.create(
                user=user,
                title="Milestone Completed",
                message=f"You have completed the milestone: {milestone_question.text}",
            )

            return Response({"detail": "Milestone marked as completed"}, status=status.HTTP_201_CREATED)
        except MilestoneQuestion.DoesNotExist:
            return Response({"error": "Milestone question not found"}, status=status.HTTP_404_NOT_FOUND)
        except MilestoneOption.DoesNotExist:
            return Response({"error": "Milestone option not found"}, status=status.HTTP_404_NOT_FOUND)


# Initialize AI counselor instance
counselor = AICounselor()

class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Handle chat messages, process them with the AI counselor, and return the response.
        Save the conversation and messages to the database for text-based conversations.
        For voice-based conversations, only return the AI's response.
        """
        # Deserialize incoming message (user message only)
        conversation_type = request.data.get('conversation_type', 'text')  # default to 'text' if not specified
        
        # If the conversation type is text, proceed with saving the conversation and messages
        if conversation_type == 'text':
            serializer = MessageSerializer(data=request.data)
            user = request.user
            if user.first_name:
                user = user.first_name
            elif user.username:
                user = user.username    
            else:   
                user = request.user

            if serializer.is_valid():
                # Extract the user message
                user_message = serializer.validated_data['content']

                # Start or retrieve the conversation for the user (we'll use 'guest' if no authenticated user)
                user_id = request.user.id if request.user.is_authenticated else "guest"
                conversation, created = Conversation.objects.get_or_create(user_id=user_id)

                # Save the user message to the database with 'role' as 'user'
                user_message_instance = Message.objects.create(
                    conversation=conversation,
                    role='user',  # The user message has the role 'user'
                    content=user_message,  # The content of the user message
                )

                # Get the AI's response
                ai_response = counselor.process_message(user_message)

                # Save the AI response to the database with 'role' as 'ai'
                ai_message_instance = Message.objects.create(
                    conversation=conversation,
                    role='ai',  # The AI message has the role 'ai'
                    content=ai_response,  # The content of the AI's response
                )
                
                # Return the AI's response to the user
                return Response({
                    "response": ai_response,  # The AI's response
                    # "conversation_id": conversation.id  # The ID of the current conversation
                })

            # Return errors if serializer is invalid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If the conversation type is voice, only return the AI response without saving
        elif conversation_type == 'voice':
            user_message = request.data.get('content', '')  # Assuming the user sends the voice content as text
            
            # Handle the AI response for the voice-based conversation
            ai_response = counselor.process_message(user_message)

            # Return the AI response directly to the frontend (no database saving)
            return Response({
                "response": ai_response,  # The AI's response
            })

        # If the conversation type is not recognized, return an error
        return Response({
            "error": "Invalid conversation type. Must be either 'text' or 'voice'."
        }, status=status.HTTP_400_BAD_REQUEST)


class ConversationHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    """
    List all conversations for a particular user.
    """
    serializer_class = ConversationSerializer

    def get_queryset(self):
        # Get the user ID from the authenticated user, or default to 'guest' if unauthenticated
        user_id = self.request.user.id if self.request.user.is_authenticated else "guest"
        # Return the conversations for the authenticated user or guest
        return Conversation.objects.filter(user_id=user_id)