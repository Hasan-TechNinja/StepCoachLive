import stripe
from tokenize import TokenError
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone 
from datetime import timedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login

from api.serializers import PasswordVerifySerializer, RegistrationSerializer, EmailTokenObtainPairSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ProfileSerializer, AddictionSerializer, SubscriptionPlanSerializer, TimerSerializer, UserSubscriptionSerializer, ProgressQuestionSerializer, ProgressAnswerSerializer, ProgressResponseSerializer, ProgressQuestionSerializer, ReportSerializer, PrivacyPolicySerializer, TermsConditionsSerializer, SupportContactSerializer
from main.models import EmailVerification, Profile, Addiction, UsageTracking, OnboardingData, ProgressQuestion, ProgressAnswer, ProgressResponse, Report, Timer, PrivacyPolicy, TermsConditions, SupportContact
from subscription.models import SubscriptionPlan, UserSubscription

from rest_framework import status, permissions
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
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate refresh token and access token using Simple JWT
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({'access': str(access_token)}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  

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
                    # 'access': str(access_token),
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
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password reset code sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)
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
            if hasattr(user, 'usagetracking'):  # Check if the user has a related UsageTracking
                user.usagetracking.delete()  # Deletes UsageTracking entry for the user
            if hasattr(user, 'onboardingdata'):  # Directly access onboardingdata (since it's OneToOneField)
                user.onboardingdata.delete()  # Deletes OnboardingData entry for the user

            # Finally, delete the user account from the User table
            user.delete()

            return Response({'detail': 'Account deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

        return Response(password_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

class AddictionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the current user's addiction data."""
        user = request.user

        addiction = Addiction.objects.filter(user=user).first()

        if addiction:
            addiction_data = AddictionSerializer(addiction).data
            return Response(addiction_data, status=status.HTTP_200_OK)
        return Response({'detail': 'No addiction data found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        """Update the current user's addiction data."""
        user = request.user

        addiction = Addiction.objects.filter(user=user).first()

        if addiction:
            serializer = AddictionSerializer(addiction, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'detail': 'No addiction data found.'}, status=status.HTTP_404_NOT_FOUND)
    

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

        # Try to find an existing active subscription and update it, if any
        try:
            user_subscription = UserSubscription.objects.get(user=user, is_active=True)
            # If an active subscription exists, update its details
            user_subscription.plan = plan
            user_subscription.start_date = timezone.now()  # Update to current time
            user_subscription.is_active = False  # Mark it as inactive for now (pending payment)
            user_subscription.save()
        except UserSubscription.DoesNotExist:
            # No active subscription found, so create a new one
            user_subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                is_active=False,  # Initially inactive, waiting for successful payment
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
                        'unit_amount': int(plan.price * 100),  # Convert to pence
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(f'/payments/success/{user_subscription.id}/'),
                cancel_url=request.build_absolute_uri('/payments/cancel/'),
                metadata={
                    'user_id': user.id,
                    'plan_id': plan.id,
                    'subscription_id': user_subscription.id  # Store subscription ID for later processing
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

        return Response({
            "saved": saved,
            "errors": errors
        }, status=status.HTTP_201_CREATED if saved else status.HTTP_400_BAD_REQUEST)
    

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
            return Response({"message": "Timer restarted", "elapsed_time": timer.get_elapsed_time()}, status=status.HTTP_200_OK)
        except Timer.DoesNotExist:
            return Response({"error": "Timer not found for this user"}, status=status.HTTP_404_NOT_FOUND)