from django.test import TestCase
from django.urls import reverse

from .models import JobSeekerProfile, User


class AccountFlowTests(TestCase):
    def test_job_seeker_signup_creates_profile(self):
        response = self.client.post(reverse('accounts.signup'), {
            'username': 'newseeker',
            'role': User.Role.JOB_SEEKER,
            'password1': 'A-secure-test-password-234',
            'password2': 'A-secure-test-password-234',
        })

        self.assertRedirects(response, reverse('accounts.login'))
        user = User.objects.get(username='newseeker')
        self.assertTrue(JobSeekerProfile.objects.filter(user=user).exists())

    def test_login_sends_each_role_to_its_workspace(self):
        seeker = User.objects.create_user(
            username='seeker', password='password', role=User.Role.JOB_SEEKER
        )
        recruiter = User.objects.create_user(
            username='recruiter', password='password', role=User.Role.RECRUITER
        )

        response = self.client.post(reverse('accounts.login'), {
            'username': seeker.username,
            'password': 'password',
        })
        self.assertRedirects(response, reverse('jobs.explore'))
        self.client.logout()

        response = self.client.post(reverse('accounts.login'), {
            'username': recruiter.username,
            'password': 'password',
        })
        self.assertRedirects(response, reverse('jobs.my_job_postings'))

    def test_logout_requires_post(self):
        user = User.objects.create_user(
            username='seeker', password='password', role=User.Role.JOB_SEEKER
        )
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('accounts.logout')).status_code, 405)
