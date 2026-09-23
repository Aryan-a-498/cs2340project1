from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
  class Role(models.TextChoices):
    JOB_SEEKER = 'job_seeker', 'Job Seeker'
    RECRUITER = 'recruiter', 'Recruiter'

  role = models.CharField(max_length=20, choices=Role.choices)

class JobSeekerProfile(models.Model):
  user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_seeker_profile')
  skills = models.ManyToManyField('jobs.Skill', related_name='job_seekers')

  def __str__(self):
    return str(self.user)