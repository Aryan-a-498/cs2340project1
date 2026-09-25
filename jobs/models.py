from math import asin, cos, radians, sin, sqrt

from django.db import models
from django.conf import settings


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobPosting(models.Model):
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    company = models.ForeignKey(
        'accounts.Company',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='job_postings',
    )
    description = models.TextField(blank=True)
    skills_required = models.ManyToManyField(Skill, related_name='job_postings')
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_postings',
    )
    location = models.CharField(max_length=255, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def recommended_candidates(self):
        scores = {}
        for skill in self.skills_required.all():
            for profile in skill.job_seekers.all():
                scores[profile] = scores.get(profile, 0) + 1

        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        return [profile for profile, count in ranked]

    def distance_from(self, latitude, longitude):
        """Return the great-circle distance from a point in miles."""
        if self.latitude is None or self.longitude is None:
            return None

        earth_radius_miles = 3958.8
        latitude_1 = radians(latitude)
        latitude_2 = radians(self.latitude)
        latitude_delta = radians(self.latitude - latitude)
        longitude_delta = radians(self.longitude - longitude)
        haversine = (
            sin(latitude_delta / 2) ** 2
            + cos(latitude_1) * cos(latitude_2) * sin(longitude_delta / 2) ** 2
        )
        return 2 * earth_radius_miles * asin(sqrt(haversine))

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        REVIEWING = 'reviewing', 'Reviewing'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        NOT_SELECTED = 'not_selected', 'Not selected'

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    applicant = models.ForeignKey(
        'accounts.JobSeekerProfile',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    cover_note = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'applicant'],
                name='unique_job_application',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.applicant} — {self.job}'
