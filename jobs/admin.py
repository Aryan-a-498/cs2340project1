from django.contrib import admin
from .models import JobApplication, JobPosting, Skill

# Register your models here.
admin.site.register(Skill)
admin.site.register(JobPosting)
admin.site.register(JobApplication)
