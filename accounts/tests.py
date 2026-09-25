from django.test import TestCase
from django.urls import reverse

from .models import Company, JobSeekerProfile, User
from jobs.models import Skill


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
        self.assertIsNone(user.company)

    def test_recruiter_signup_joins_company(self):
        response = self.client.post(reverse('accounts.signup'), {
            'username': 'newrecruiter',
            'role': User.Role.RECRUITER,
            'company_name': 'Scoutly Labs',
            'password1': 'A-secure-test-password-234',
            'password2': 'A-secure-test-password-234',
        })

        self.assertRedirects(response, reverse('accounts.login'))
        user = User.objects.get(username='newrecruiter')
        self.assertEqual(user.company.name, 'Scoutly Labs')
        self.assertTrue(Company.objects.filter(name='Scoutly Labs').exists())

    def test_recruiter_signup_requires_company(self):
        response = self.client.post(reverse('accounts.signup'), {
            'username': 'newrecruiter',
            'role': User.Role.RECRUITER,
            'password1': 'A-secure-test-password-234',
            'password2': 'A-secure-test-password-234',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter the company you are recruiting for.')

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

    def test_job_seeker_can_update_searchable_profile(self):
        user = User.objects.create_user(
            username='seeker', password='password', role=User.Role.JOB_SEEKER
        )
        profile = JobSeekerProfile.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.post(reverse('accounts.profile'), {
            'skills': 'Python, Django, python',
            'projects': 'Built a transit analytics dashboard with Django.',
        })

        self.assertRedirects(response, reverse('accounts.profile'))
        profile.refresh_from_db()
        self.assertEqual(
            profile.projects,
            'Built a transit analytics dashboard with Django.',
        )
        self.assertEqual(
            set(profile.skills.values_list('name', flat=True)),
            {'Python', 'Django'},
        )
        self.assertEqual(Skill.objects.count(), 2)

    def test_recruiter_cannot_edit_candidate_profile(self):
        recruiter = User.objects.create_user(
            username='recruiter', role=User.Role.RECRUITER
        )
        self.client.force_login(recruiter)

        response = self.client.get(reverse('accounts.profile'))

        self.assertEqual(response.status_code, 403)
