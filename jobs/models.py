from django.db import models
from django.conf import settings

class Skill(models.Model):
  name = models.CharField(max_length=100, unique=True)

  def __str__(self):
    return self.name

class JobPosting(models.Model):
  title = models.CharField(max_length=255)
  company_name = models.CharField(max_length=255)
  skills_required = models.ManyToManyField(Skill, related_name='job_postings')
  posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_postings')
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

  def __str__(self):
    return self.title
