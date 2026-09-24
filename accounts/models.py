from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator


class User(AbstractUser):
    class Role(models.TextChoices):
        JOB_SEEKER = 'job_seeker', 'Job Seeker'
        RECRUITER = 'recruiter', 'Recruiter'

    role = models.CharField(max_length=20, choices=Role.choices)


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_seeker_profile',
    )
    skills = models.ManyToManyField(
        'jobs.Skill',
        related_name='job_seekers',
        blank=True,
    )
    location = models.CharField(max_length=255, blank=True)
    preferred_latitude = models.FloatField(null=True, blank=True)
    preferred_longitude = models.FloatField(null=True, blank=True)
    commute_radius_miles = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    cart_jobs = models.ManyToManyField(
        'jobs.JobPosting',
        related_name='in_job_seeker_carts',
        blank=True,
    )

    def __str__(self):
        return str(self.user)
