from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import JobTitle

CustomUser = get_user_model()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'job_title']
    ordering = ('email',)  # Fix: Order users by email instead of username

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        # Removed 'email' to avoid duplicates
        ('Personal info', {
         'fields': ('first_name', 'last_name', 'job_title')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "job_title"),
            },
        ),
    )


class JobTitleAdmin(admin.ModelAdmin):
    model = JobTitle
    fields = ['title', 'description']
    list_display = ['title', 'description']


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(JobTitle, JobTitleAdmin)
