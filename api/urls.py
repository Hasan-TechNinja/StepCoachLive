# urls.py - Complete the URL configuration for the API
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'user-subscriptions', views.UserSubscriptionViewSet, basename='user-subscription')

urlpatterns = [
    # Auth-related paths
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('login/', views.EmailLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('addiction/', views.AddictionView.as_view(), name='addiction'),

    path('subscription-plans/', views.SubscriptionPlanView.as_view(), name='report'),
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('', include(router.urls)),

    path('progress-test/', views.UserProgressTest.as_view(), name='progress-questions'),
    path('progress/submit/', views.SubmitProgressResponses.as_view(), name='submit-progress-responses'),
    path('progress/result/', views.ProgressResultView.as_view(), name='progress-result/'),
]

# Static files handling (e.g., media files)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
