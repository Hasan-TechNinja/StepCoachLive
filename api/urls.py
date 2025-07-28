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
    path('resend-verification-code/', views.ResendVerificationCodeView.as_view(), name='resend-verification-code'),
    path('login/', views.EmailLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-conditions/', views.TermsConditionsView.as_view(), name='terms_conditions'),
    path('support-contact/', views.SupportContactView.as_view(), name='support_contact'),

    path('subscription-plans/', views.SubscriptionPlanView.as_view(), name='report'),
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('', include(router.urls)),

    path('progress-test/', views.UserProgressTest.as_view(), name='progress-questions'),
    path('progress/submit/', views.SubmitProgressResponses.as_view(), name='submit-progress-responses'),
    path('progress/result/', views.ProgressResultView.as_view(), name='progress-result/'),
    path('report/', views.ReportView.as_view(), name='report'),

    path('timer/', views.TimerView.as_view(), name='get_timer'),
    path('restart-timer/', views.RestartTimerView.as_view(), name='restart_timer'),

    path('addictions/', views.AddictionView.as_view(), name='addiction-selection'),
    path('addictions/<int:pk>', views.AddictionDetailsView.as_view(), name='addiction'),
    # path('goals/', views.GoalSelectionView.as_view(), name='goal-selection'),
    # path('milestones/', views.MilestoneSelectionView.as_view(), name='milestone-selection'),
    path('drinking-habits/', views.DrinkingHabitsView.as_view(), name='drinking-habits'),
    path('triggers-text/', views.TriggersTextView.as_view(), name='triggers-text'),
    # path('day-per-week/', views.AddictionWeekView.as_view()),
    path('drinks-rate/', views.DrinksRateView.as_view()),
    path('trigger-text/', views.TriggerTextView.as_view()),
    path('improveQA/', views.ImproveQuestionAnswerView.as_view()),
    path('milestoneSA/', views.MilestoneQuestionAnswerView.as_view()),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),

    path('journals/', views.JournalEntryView.as_view(), name='journal-entries'),
    path('journals/<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal-entry-detail'),
    path('daily/', views.DailyInspirationAPIView.as_view(), name='daily-inspiration'),
    
    path('suggestions/', views.SuggestionLiarView.as_view(), name='suggestions'),
    path('suggestions/<int:pk>', views.SuggestionDetailsView.as_view(), name='suggestions'),
    path('suggestions/<int:pk>/<int:id>', views.SuggestionVideoView.as_view(), name='suggestion-categories'),
    path('suggestions-popular/', views.PopularSuggestionView.as_view(), name='suggestion-categories'),
    path('suggestion-recent/', views.RecentSuggestionView.as_view(), name='suggestion-categories'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/', views.MarkNotificationsReadView.as_view(), name='notifications-mark-read'),
]

# Static files handling (e.g., media files)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
