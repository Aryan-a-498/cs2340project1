from django.test import TestCase
from django.urls import reverse

from accounts.models import JobSeekerProfile, User
from jobs.models import JobPosting
from .models import Conversation, Message


class MessagingTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='recruiter',
            password='password',
            first_name='Riley',
            last_name='Hart',
            role=User.Role.RECRUITER,
        )
        self.other_recruiter = User.objects.create_user(
            username='other-recruiter',
            password='password',
            role=User.Role.RECRUITER,
        )
        self.seeker = User.objects.create_user(
            username='candidate',
            password='password',
            first_name='Jamie',
            last_name='Rivera',
            role=User.Role.JOB_SEEKER,
        )
        JobSeekerProfile.objects.create(user=self.seeker)
        self.job = JobPosting.objects.create(
            title='Junior Developer',
            company_name='Scoutly Labs',
            posted_by=self.recruiter,
        )
        self.client.force_login(self.recruiter)

    def _start_conversation(self):
        return self.client.post(
            reverse('messaging.start', args=[self.seeker.id]),
            {'job': self.job.id},
        )

    def test_recruiter_can_start_one_conversation_per_candidate(self):
        response = self._start_conversation()
        conversation = Conversation.objects.get()

        self.assertRedirects(response, reverse(
            'messaging.conversation',
            args=[conversation.id],
        ))
        self.assertEqual(conversation.recruiter, self.recruiter)
        self.assertEqual(conversation.job_seeker, self.seeker)
        self.assertEqual(conversation.job, self.job)

        self._start_conversation()
        self.assertEqual(Conversation.objects.count(), 1)

    def test_job_seeker_cannot_start_conversation(self):
        self.client.force_login(self.seeker)
        response = self.client.post(
            reverse('messaging.start', args=[self.recruiter.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Conversation.objects.exists())

    def test_recruiter_can_only_message_job_seekers(self):
        response = self.client.post(
            reverse('messaging.start', args=[self.other_recruiter.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_recruiter_cannot_attach_another_recruiters_job(self):
        other_job = JobPosting.objects.create(
            title='Other Job',
            company_name='Other Company',
            posted_by=self.other_recruiter,
        )
        response = self.client.post(
            reverse('messaging.start', args=[self.seeker.id]),
            {'job': other_job.id},
        )
        self.assertEqual(response.status_code, 404)

    def test_both_participants_can_send_messages(self):
        self._start_conversation()
        conversation = Conversation.objects.get()
        url = reverse('messaging.conversation', args=[conversation.id])

        self.client.post(url, {'body': 'Are you free for an interview?'})
        self.client.force_login(self.seeker)
        response = self.client.post(url, {'body': 'Yes, Tuesday works.'})

        self.assertRedirects(response, url)
        self.assertEqual(
            list(conversation.messages.values_list('body', flat=True)),
            ['Are you free for an interview?', 'Yes, Tuesday works.'],
        )

    def test_empty_message_is_rejected(self):
        self._start_conversation()
        conversation = Conversation.objects.get()
        response = self.client.post(
            reverse('messaging.conversation', args=[conversation.id]),
            {'body': ''},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.exists())

    def test_outsiders_cannot_read_conversation(self):
        self._start_conversation()
        conversation = Conversation.objects.get()
        self.client.force_login(self.other_recruiter)

        self.assertEqual(
            self.client.get(reverse(
                'messaging.conversation',
                args=[conversation.id],
            )).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse(
                'messaging.conversation_updates',
                args=[conversation.id],
            )).status_code,
            404,
        )

    def test_unread_count_clears_after_opening_conversation(self):
        self._start_conversation()
        conversation = Conversation.objects.get()
        Message.objects.create(
            conversation=conversation,
            sender=self.recruiter,
            body='Hello from Scoutly Labs!',
        )
        self.client.force_login(self.seeker)

        response = self.client.get(reverse('messaging.inbox'))
        self.assertEqual(response.context['unread_conversation_count'], 1)

        self.client.get(reverse('messaging.conversation', args=[conversation.id]))
        response = self.client.get(reverse('messaging.inbox'))
        self.assertEqual(response.context['unread_conversation_count'], 0)

    def test_updates_only_return_newer_messages(self):
        self._start_conversation()
        conversation = Conversation.objects.get()
        first = Message.objects.create(
            conversation=conversation,
            sender=self.recruiter,
            body='First message',
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.seeker,
            body='Second message',
        )

        response = self.client.get(
            reverse('messaging.conversation_updates', args=[conversation.id]),
            {'after': first.id},
        )
        data = response.json()['messages']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['body'], 'Second message')
        self.assertFalse(data[0]['is_mine'])

    def test_message_button_only_shows_for_recruiters(self):
        self._start_conversation()
        conversation = Conversation.objects.get()
        self.client.force_login(self.seeker)
        response = self.client.get(reverse('messaging.inbox'))

        self.assertContains(response, 'Riley Hart')
        self.assertNotContains(response, reverse('messaging.start', args=[self.seeker.id]))
        self.assertContains(response, reverse('messaging.conversation', args=[conversation.id]))
