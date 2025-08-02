from django.contrib import admin
from . models import *

# Register your models here.

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    search_fields = ('user__email', 'code') 
    list_filter = ('created_at',)
admin.site.register(EmailVerification, EmailVerificationAdmin)


class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    search_fields = ('user__email', 'code')
    list_filter = ('created_at',)
admin.site.register(PasswordResetCode, PasswordResetCodeAdmin)  

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'joined_date')
    search_fields = ('user__email',)
    list_filter = ('joined_date',)  
admin.site.register(Profile, ProfileAdmin)


class AddictionAdmin(admin.ModelAdmin):
    list_display = ('addiction_type', 'created_at')
    search_fields = ('addiction_type',)
    list_filter = ('created_at',)   
admin.site.register(Addiction, AddictionAdmin)


admin.site.register(AddictionOption)
# admin.site.register(GoalOption)
# admin.site.register(MilestoneOption)


class OnboardingDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'days_per_week', 'drinks_per_day','completed'
    )

admin.site.register(OnboardingData, OnboardingDataAdmin)


class ProgressAnswerInline(admin.TabularInline):
    model = ProgressAnswer
    extra = 5

class ProgressQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('text',)
    inlines = [ProgressAnswerInline]
admin.site.register(ProgressQuestion, ProgressQuestionAdmin)

class ProgressAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text')
    list_filter = ('question',)
    search_fields = ('text',)

admin.site.register(ProgressAnswer, ProgressAnswerAdmin)


class ProgressResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'answer', 'created_at')
    list_filter = ('user', 'question')
    search_fields = ('user__email', 'question__text', 'answer__text')

admin.site.register(ProgressResponse, ProgressResponseAdmin)


class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'file', 'title', 'uploaded_at'
    )
    search_fields = ('user__email', 'title')
    list_filter = ('uploaded_at',)

admin.site.register(Report, ReportAdmin)


class TimerAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'start_time', 'last_restart_time'
    )
    search_fields = ('user__email',)
    list_filter = ('start_time', 'last_restart_time')
admin.site.register(Timer, TimerAdmin)


class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_updated')
    search_fields = ('name',)
    list_filter = ('last_updated',)
admin.site.register(PrivacyPolicy, PrivacyPolicyAdmin)

class TermsConditionsAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_updated')
    search_fields = ('name',)
    list_filter = ('last_updated',)
admin.site.register(TermsConditions, TermsConditionsAdmin)


class SupportContactAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_primary', 'phone_secondary')
    search_fields = ('email', 'phone_primary', 'phone_secondary')
    list_filter = ('email',)
admin.site.register(SupportContact, SupportContactAdmin)


class ImproveQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'text', 'created'
    )
    # list_filter = ('created')
admin.site.register(ImproveQuestion, ImproveQuestionAdmin)


class ImproveQuestionOptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'question', 'text', 'created'
    )

admin.site.register(ImproveQuestionOption, ImproveQuestionOptionAdmin)


class MilestoneQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'text', 'created'
    )
    # list_filter = ('created')
admin.site.register(MilestoneQuestion, MilestoneQuestionAdmin)


class MilestoneOptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'question', 'text', 'created'
    )

admin.site.register(MilestoneOption, MilestoneOptionAdmin)


class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'content', 'created_at', 'updated_at')
    search_fields = ('user__email', 'title')
    list_filter = ('created_at', 'updated_at')  
admin.site.register(JournalEntry, JournalEntryAdmin)


class QuoteAdmin(admin.ModelAdmin):
    list_display = ('date', 'text', 'author')
    search_fields = ('text', 'author')
    list_filter = ('date',)
admin.site.register(Quote, QuoteAdmin)


@admin.register(SuggestionCategory)
class SuggestionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('category', 'text_short', 'view_count', 'created_at')
    list_filter = ('category',)
    search_fields = ('text',)
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Text Preview'



class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'title', 'message', 'is_read', 'created_at'
    )
admin.site.register(Notification, NotificationAdmin)    




class RecoveryMilestoneAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'milestone_name', 'target_date', 'completed'
    )

admin.site.register(RecoveryMilestone, RecoveryMilestoneAdmin)


class MessageInline(admin.TabularInline):
    """
    Allows for inline editing of messages within a conversation.
    """
    model = Message
    extra = 1  # Add 1 empty form to create a new message inline
    readonly_fields = ['role', 'content', 'timestamp']  # Make some fields read-only (optional)
    can_delete = False  # Disable deleting messages from the inline form

class ConversationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Conversation model.
    """
    list_display = ('user_id', 'started_at', 'last_updated')  # Fields to display in the list view
    search_fields = ('user_id',)  # Allow search by user_id
    list_filter = ('started_at',)  # Add filters based on started_at
    inlines = [MessageInline]  # Display messages inline within the conversation

class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for the Message model.
    """
    list_display = ('role', 'content', 'timestamp', 'conversation')  # Fields to display in the list view
    search_fields = ('content',)  # Allow search by content
    list_filter = ('role',)  # Add filters based on role (user or ai)
    readonly_fields = ('role', 'content', 'timestamp')  # Make some fields read-only (optional)

# Register models with the admin site
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)