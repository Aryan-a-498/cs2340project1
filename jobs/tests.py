from django.test import TestCase
from django.urls import reverse

from accounts.models import Company, JobSeekerProfile, User
from .models import JobApplication, JobPosting, Skill


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

    def test_job_seeker_can_apply_only_once(self):
        response = self.client.post(
            reverse('jobs.apply', args=[self.nearby_job.id]),
            {'cover_note': 'I have experience building Django applications.'},
        )

        self.assertRedirects(response, reverse('jobs.explore'))
        application = JobApplication.objects.get(
            job=self.nearby_job,
            applicant=self.profile,
        )
        self.assertEqual(
            application.cover_note,
            'I have experience building Django applications.',
        )

        self.client.post(
            reverse('jobs.apply', args=[self.nearby_job.id]),
            {'cover_note': 'A duplicate application.'},
        )
        self.assertEqual(
            JobApplication.objects.filter(
                job=self.nearby_job,
                applicant=self.profile,
            ).count(),
            1,
        )

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


class RecruiterJobPostingTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Scoutly Labs')
        self.recruiter = User.objects.create_user(
            username='recruiter',
            password='password',
            role=User.Role.RECRUITER,
            company=self.company,
        )
        self.other_recruiter = User.objects.create_user(
            username='other-recruiter',
            password='password',
            role=User.Role.RECRUITER,
        )
        self.seeker = User.objects.create_user(
            username='seeker',
            password='password',
            role=User.Role.JOB_SEEKER,
        )
        self.client.force_login(self.recruiter)

    def job_data(self, **overrides):
        data = {
            'title': 'Junior Django Developer',
            'company_name': 'Tampered Labs',
            'description': (
                'Build internal Django tools for early-career hiring teams.'
            ),
            'location': 'Atlanta, GA',
            'latitude': '33.749',
            'longitude': '-84.388',
            'required_skills': 'Python, Django, SQL',
        }
        data.update(overrides)
        return data

    def test_recruiter_can_post_a_job(self):
        response = self.client.post(reverse('jobs.create'), self.job_data())

        self.assertRedirects(response, reverse('jobs.my_job_postings'))
        job = JobPosting.objects.get(title='Junior Django Developer')
        self.assertEqual(job.posted_by, self.recruiter)
        self.assertEqual(job.company_name, 'Scoutly Labs')
        self.assertEqual(job.company, self.company)
        self.assertEqual(
            job.description,
            'Build internal Django tools for early-career hiring teams.',
        )
        self.assertEqual(
            set(job.skills_required.values_list('name', flat=True)),
            {'Python', 'Django', 'SQL'},
        )

    def test_recruiter_can_edit_an_owned_job(self):
        python = Skill.objects.create(name='Python')
        job = JobPosting.objects.create(
            title='Developer',
            company_name='Scoutly Labs',
            posted_by=self.recruiter,
            location='Atlanta, GA',
            latitude=33.749,
            longitude=-84.388,
        )
        job.skills_required.add(python)

        response = self.client.post(
            reverse('jobs.edit', args=[job.id]),
            self.job_data(
                title='Software Engineer',
                description='Own integrations for recruiter workflows.',
                required_skills='Python, REST APIs',
            ),
        )

        self.assertRedirects(response, reverse('jobs.my_job_postings'))
        job.refresh_from_db()
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.company_name, 'Scoutly Labs')
        self.assertEqual(job.company, self.company)
        self.assertEqual(
            job.description,
            'Own integrations for recruiter workflows.',
        )
        self.assertEqual(
            set(job.skills_required.values_list('name', flat=True)),
            {'Python', 'REST APIs'},
        )

    def test_recruiter_cannot_edit_another_recruiters_job(self):
        job = JobPosting.objects.create(
            title='Private posting',
            company_name='Other Company',
            posted_by=self.other_recruiter,
        )

        response = self.client.get(reverse('jobs.edit', args=[job.id]))

        self.assertEqual(response.status_code, 404)

    def test_job_seeker_cannot_create_or_edit_jobs(self):
        job = JobPosting.objects.create(
            title='Developer',
            company_name='Scoutly Labs',
            posted_by=self.recruiter,
        )
        self.client.force_login(self.seeker)

        self.assertEqual(self.client.get(reverse('jobs.create')).status_code, 403)
        self.assertEqual(
            self.client.get(reverse('jobs.edit', args=[job.id])).status_code,
            403,
        )

    def test_job_requires_a_map_location(self):
        response = self.client.post(
            reverse('jobs.create'),
            self.job_data(latitude='', longitude=''),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose the job location on the map.')
        self.assertFalse(JobPosting.objects.exists())


class RecruiterApplicationTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='recruiter',
            password='password',
            role=User.Role.RECRUITER,
        )
        self.other_recruiter = User.objects.create_user(
            username='other-recruiter',
            password='password',
            role=User.Role.RECRUITER,
        )
        self.seeker = User.objects.create_user(
            username='candidate',
            first_name='Jamie',
            last_name='Rivera',
            email='jamie@example.com',
            role=User.Role.JOB_SEEKER,
        )
        self.profile = JobSeekerProfile.objects.create(
            user=self.seeker,
            location='Midtown Atlanta, GA',
            projects='Built a transit analytics dashboard with Django.',
            preferred_latitude=33.781,
            preferred_longitude=-84.388,
        )
        self.python = Skill.objects.create(name='Python')
        self.django = Skill.objects.create(name='Django')
        self.profile.skills.add(self.python)
        self.job = JobPosting.objects.create(
            title='Junior Developer',
            company_name='Scoutly Labs',
            posted_by=self.recruiter,
            location='Atlanta, GA',
        )
        self.job.skills_required.add(self.python, self.django)
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.profile,
            cover_note='I enjoy solving useful problems with Python.',
        )
        self.client.force_login(self.recruiter)

    def test_recruiter_can_review_profile_and_application_together(self):
        response = self.client.get(reverse(
            'jobs.application_detail',
            args=[self.job.id, self.application.id],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jamie Rivera')
        self.assertContains(response, 'jamie@example.com')
        self.assertContains(response, 'Midtown Atlanta, GA')
        self.assertContains(response, 'transit analytics dashboard')
        self.assertContains(response, self.application.cover_note)
        self.assertEqual(response.context['matched_skills'], [self.python])

    def test_recruiter_can_update_application_status(self):
        response = self.client.post(
            reverse(
                'jobs.application_detail',
                args=[self.job.id, self.application.id],
            ),
            {'status': JobApplication.Status.SHORTLISTED},
        )

        self.assertRedirects(response, reverse(
            'jobs.application_detail',
            args=[self.job.id, self.application.id],
        ))
        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.SHORTLISTED,
        )

    def test_recruiter_cannot_review_another_recruiters_application(self):
        self.client.force_login(self.other_recruiter)
        response = self.client.get(reverse(
            'jobs.application_detail',
            args=[self.job.id, self.application.id],
        ))
        self.assertEqual(response.status_code, 404)

    def test_applicant_map_clusters_nearby_candidates(self):
        second_user = User.objects.create_user(
            username='second-candidate',
            role=User.Role.JOB_SEEKER,
        )
        second_profile = JobSeekerProfile.objects.create(
            user=second_user,
            location='Midtown Atlanta, GA',
            preferred_latitude=33.782,
            preferred_longitude=-84.386,
        )
        JobApplication.objects.create(job=self.job, applicant=second_profile)

        response = self.client.get(reverse('jobs.applicant_map'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['applicant_count'], 2)
        self.assertEqual(response.context['located_applicant_count'], 2)
        self.assertEqual(len(response.context['clusters']), 1)
        self.assertEqual(response.context['clusters'][0]['count'], 2)

    def test_applicant_map_only_includes_owned_job_applications(self):
        other_job = JobPosting.objects.create(
            title='Other Job',
            company_name='Other Company',
            posted_by=self.other_recruiter,
        )
        other_user = User.objects.create_user(
            username='outside-candidate',
            role=User.Role.JOB_SEEKER,
        )
        other_profile = JobSeekerProfile.objects.create(
            user=other_user,
            preferred_latitude=33.9,
            preferred_longitude=-84.4,
        )
        JobApplication.objects.create(job=other_job, applicant=other_profile)

        response = self.client.get(reverse('jobs.applicant_map'))
        self.assertEqual(response.context['applicant_count'], 1)

    def test_job_seeker_cannot_access_recruiter_application_pages(self):
        self.client.force_login(self.seeker)
        self.assertEqual(
            self.client.get(reverse('jobs.applicant_map')).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse(
                'jobs.applications',
                args=[self.job.id],
            )).status_code,
            403,
        )


class CandidateSearchTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='recruiter',
            password='password',
            role=User.Role.RECRUITER,
        )
        self.atlanta_user = User.objects.create_user(
            username='atlanta-candidate',
            first_name='Avery',
            last_name='Morgan',
            email='avery@example.com',
            role=User.Role.JOB_SEEKER,
        )
        self.atlanta_profile = JobSeekerProfile.objects.create(
            user=self.atlanta_user,
            location='Midtown Atlanta, GA',
            projects=(
                'Built a transit analytics dashboard with React and Django.'
            ),
        )
        self.seattle_user = User.objects.create_user(
            username='seattle-candidate',
            first_name='Jordan',
            last_name='Lee',
            role=User.Role.JOB_SEEKER,
        )
        self.seattle_profile = JobSeekerProfile.objects.create(
            user=self.seattle_user,
            location='Seattle, WA',
            projects='Created an iOS garden journal using Swift.',
        )
        python = Skill.objects.create(name='Python')
        django = Skill.objects.create(name='Django')
        swift = Skill.objects.create(name='Swift')
        self.atlanta_profile.skills.add(python, django)
        self.seattle_profile.skills.add(swift)
        self.client.force_login(self.recruiter)

    def candidate_ids(self, response):
        return set(response.context['candidates'].values_list('id', flat=True))

    def test_candidate_directory_shows_all_job_seekers_by_default(self):
        response = self.client.get(reverse('jobs.candidate_search'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.candidate_ids(response),
            {self.atlanta_profile.id, self.seattle_profile.id},
        )

    def test_recruiter_can_filter_candidates_by_each_search_field(self):
        skills_response = self.client.get(
            reverse('jobs.candidate_search'),
            {'skills': 'python'},
        )
        location_response = self.client.get(
            reverse('jobs.candidate_search'),
            {'location': 'seattle'},
        )
        projects_response = self.client.get(
            reverse('jobs.candidate_search'),
            {'projects': 'analytics'},
        )

        self.assertEqual(
            self.candidate_ids(skills_response),
            {self.atlanta_profile.id},
        )
        self.assertEqual(
            self.candidate_ids(location_response),
            {self.seattle_profile.id},
        )
        self.assertEqual(
            self.candidate_ids(projects_response),
            {self.atlanta_profile.id},
        )

    def test_combined_filters_and_comma_separated_terms_all_match(self):
        response = self.client.get(reverse('jobs.candidate_search'), {
            'skills': 'Python, Django',
            'location': 'Atlanta',
            'projects': 'analytics, React',
        })

        self.assertEqual(
            self.candidate_ids(response),
            {self.atlanta_profile.id},
        )
        self.assertTrue(response.context['has_filters'])

    def test_job_seeker_cannot_search_candidates(self):
        self.client.force_login(self.atlanta_user)

        response = self.client.get(reverse('jobs.candidate_search'))

        self.assertEqual(response.status_code, 403)
