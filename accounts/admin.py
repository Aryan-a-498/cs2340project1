from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Company, JobSeekerProfile, User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'company')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'company')}),
    )

admin.site.register(Company)
admin.site.register(User, CustomUserAdmin)
admin.site.register(JobSeekerProfile)
