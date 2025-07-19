from django.contrib import admin
from . models import EmailVerification

# Register your models here.

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    search_fields = ('user__email', 'code') 
    list_filter = ('created_at',)
admin.site.register(EmailVerification, EmailVerificationAdmin)