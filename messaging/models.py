from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from accounts.models import User


class Conversation(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruiter_conversations',
    )
    job_seeker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_seeker_conversations',
    )
    job = models.ForeignKey(
        'jobs.JobPosting',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
    )
    recruiter_last_read_at = models.DateTimeField(null=True, blank=True)
    job_seeker_last_read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recruiter', 'job_seeker'],
                name='unique_conversation_pair',
            ),
        ]
        ordering = ['-updated_at']

    @staticmethod
    def last_read_field(user):
        if user.role == User.Role.RECRUITER:
            return 'recruiter_last_read_at'
        return 'job_seeker_last_read_at'

    @classmethod
    def for_user(cls, user):
        return cls.objects.filter(Q(recruiter=user) | Q(job_seeker=user))

    def other_participant(self, user):
        return self.job_seeker if user == self.recruiter else self.recruiter

    def mark_read(self, user):
        field = self.last_read_field(user)
        setattr(self, field, timezone.now())
        self.save(update_fields=[field])

    def __str__(self):
        return f'{self.recruiter} ↔ {self.job_seeker}'


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    @classmethod
    def unread_for(cls, user):
        """Messages sent to a user after they last opened the conversation."""
        field = f'conversation__{Conversation.last_read_field(user)}'
        return cls.objects.filter(
            Q(conversation__recruiter=user) | Q(conversation__job_seeker=user)
        ).exclude(sender=user).filter(
            Q(**{f'{field}__isnull': True}) | Q(created_at__gt=F(field))
        )

    def __str__(self):
        return f'{self.sender}: {self.body[:40]}'
