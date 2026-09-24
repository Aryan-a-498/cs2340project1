from django.test import TestCase
from django.urls import reverse

from accounts.models import JobSeekerProfile, User
from .models import JobPosting


class JobSeekerJobTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='recruiter',
            password='password',
            role=User.Role.RECRUITER,
        )
        self.seeker = User.objects.create_user(
            username='seeker',
            password='password',
            role=User.Role.JOB_SEEKER,
        )
        self.profile = JobSeekerProfile.objects.create(
            user=self.seeker,
            preferred_latitude=33.749,
            preferred_longitude=-84.388,
            commute_radius_miles=10,
        )
        self.nearby_job = JobPosting.objects.create(
            title='Junior Developer',
            company_name='Peachtree Software',
            posted_by=self.recruiter,
            location='Atlanta, GA',
            latitude=33.760,
            longitude=-84.390,
        )
        self.distant_job = JobPosting.objects.create(
            title='Data Analyst',
            company_name='River Analytics',
            posted_by=self.recruiter,
            location='Chattanooga, TN',
            latitude=35.0456,
            longitude=-85.3097,
        )
        self.client.force_login(self.seeker)

    def test_explore_only_returns_jobs_inside_commute_radius(self):
        response = self.client.get(reverse('jobs.explore'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.nearby_job, response.context['jobs'])
        self.assertNotIn(self.distant_job, response.context['jobs'])

    def test_job_without_coordinates_is_not_returned(self):
        job = JobPosting.objects.create(
            title='Mystery Location Role',
            company_name='Unknown',
            posted_by=self.recruiter,
        )

        response = self.client.get(reverse('jobs.explore'))
        self.assertNotIn(job, response.context['jobs'])

    def test_job_seeker_can_update_commute_preference(self):
        response = self.client.post(reverse('jobs.explore'), {
            'preferred_latitude': 33.775,
            'preferred_longitude': -84.400,
            'commute_radius_miles': 25,
        })

        self.assertRedirects(response, reverse('jobs.explore'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.preferred_latitude, 33.775)
        self.assertEqual(self.profile.preferred_longitude, -84.400)
        self.assertEqual(self.profile.commute_radius_miles, 25)

    def test_invalid_commute_preference_is_rejected(self):
        response = self.client.post(reverse('jobs.explore'), {
            'preferred_latitude': 200,
            'preferred_longitude': -84.400,
            'commute_radius_miles': 10,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose a valid location on the map.')

    def test_job_seeker_can_add_and_remove_cart_jobs(self):
        add_response = self.client.post(
            reverse('jobs.add_to_cart', args=[self.nearby_job.id])
        )
        self.assertRedirects(add_response, reverse('jobs.explore'))
        self.assertTrue(self.profile.cart_jobs.filter(id=self.nearby_job.id).exists())

        cart_response = self.client.get(reverse('jobs.cart'))
        self.assertContains(cart_response, self.nearby_job.title)

        remove_response = self.client.post(
            reverse('jobs.remove_from_cart', args=[self.nearby_job.id])
        )
        self.assertRedirects(remove_response, reverse('jobs.cart'))
        self.assertFalse(self.profile.cart_jobs.filter(id=self.nearby_job.id).exists())

    def test_cart_changes_require_post(self):
        response = self.client.get(
            reverse('jobs.add_to_cart', args=[self.nearby_job.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_recruiter_cannot_use_job_seeker_pages(self):
        self.client.force_login(self.recruiter)
        self.assertEqual(self.client.get(reverse('jobs.explore')).status_code, 403)
        self.assertEqual(self.client.get(reverse('jobs.cart')).status_code, 403)


class DistanceTests(TestCase):
    def test_distance_is_calculated_in_miles(self):
        recruiter = User.objects.create_user(
            username='recruiter', role=User.Role.RECRUITER
        )
        job = JobPosting.objects.create(
            title='Test Job',
            company_name='Test Company',
            posted_by=recruiter,
            latitude=0,
            longitude=1,
        )

        self.assertAlmostEqual(job.distance_from(0, 0), 69.1, places=1)
