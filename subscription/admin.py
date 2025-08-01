from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription
# Register your models here.

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'plan_type')
    search_fields = ('name',)
    list_filter = ('plan_type',)
    ordering = ('-price',)

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    search_fields = ('user__username', 'plan__name')
    list_filter = ('is_active', 'plan__plan_type')

admin.site.register(UserSubscription, UserSubscriptionAdmin)