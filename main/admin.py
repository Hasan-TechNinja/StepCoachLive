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
    list_display = ('user', 'addiction_type', 'created_at')
    search_fields = ('user__email', 'addiction_type')
    list_filter = ('created_at',)   
admin.site.register(Addiction, AddictionAdmin)


admin.site.register(UsageTracking)
admin.site.register(AddictionOption)
admin.site.register(GoalOption)
admin.site.register(MilestoneOption)


class OnboardingDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'days_per_week', 'drinks_per_day','completed'
    )

admin.site.register(OnboardingData, OnboardingDataAdmin)


class ProgressAnswerInline(admin.TabularInline):
    model = ProgressAnswer
    extra = 1

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