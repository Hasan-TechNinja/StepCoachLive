from tokenize import TokenError
from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from api.serializers import PasswordVerifySerializer, RegistrationSerializer, EmailTokenObtainPairSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ProfileSerializer, AddictionSerializer
from main.models import EmailVerification, Profile, Addiction, UsageTracking, OnboardingData
from django.contrib.auth.models import User
from django.utils import timezone 
from rest_framework_simplejwt.views import TokenObtainPairView

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
                verification.delete()  # Remove the verification record after successful verification
                return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
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
            # Attempt to create a RefreshToken instance from the provided token
            token = RefreshToken(refresh_token)

            # If token is valid, blacklist it
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)

        except TokenError as e:
            # Catch token errors and provide specific error message
            return Response({
                "detail": f"Invalid or expired refresh token: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        

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