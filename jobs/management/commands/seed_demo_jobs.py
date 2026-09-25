from django.core.management.base import BaseCommand

from accounts.models import JobSeekerProfile, User
from jobs.models import JobApplication, JobPosting, Skill
from messaging.models import Conversation, Message


DEMO_PASSWORD = 'ScoutlyDemo123!'


DEMO_JOBS = [
    {
        'title': 'Junior Software Engineer',
        'company_name': 'Peachtree Labs',
        'location': 'Midtown Atlanta, GA',
        'latitude': 33.7810,
        'longitude': -84.3880,
        'skills': ['Python', 'Django', 'Git'],
    },
    {
        'title': 'Product Coordinator',
        'company_name': 'Centennial Works',
        'location': 'Downtown Atlanta, GA',
        'latitude': 33.7550,
        'longitude': -84.3900,
        'skills': ['Communication', 'Project Management'],
    },
    {
        'title': 'UX Designer',
        'company_name': 'Decatur Creative',
        'location': 'Decatur, GA',
        'latitude': 33.7748,
        'longitude': -84.2963,
        'skills': ['Figma', 'User Research'],
    },
    {
        'title': 'Operations Analyst',
        'company_name': 'Runway Logistics',
        'location': 'College Park, GA',
        'latitude': 33.6534,
        'longitude': -84.4494,
        'skills': ['Excel', 'Data Analysis'],
    },
    {
        'title': 'Data Analyst',
        'company_name': 'Northline Insights',
        'location': 'Buckhead Atlanta, GA',
        'latitude': 33.8480,
        'longitude': -84.3700,
        'skills': ['Python', 'SQL', 'Data Analysis'],
    },
    {
        'title': 'QA Analyst',
        'company_name': 'Perimeter Systems',
        'location': 'Sandy Springs, GA',
        'latitude': 33.9304,
        'longitude': -84.3733,
        'skills': ['Testing', 'Git'],
    },
    {
        'title': 'Support Engineer',
        'company_name': 'Marietta Cloud',
        'location': 'Marietta, GA',
        'latitude': 33.9526,
        'longitude': -84.5499,
        'skills': ['Communication', 'Python'],
    },
    {
        'title': 'Frontend Developer',
        'company_name': 'North Point Digital',
        'location': 'Alpharetta, GA',
        'latitude': 34.0754,
        'longitude': -84.2941,
        'skills': ['JavaScript', 'HTML', 'CSS'],
    },
]

DEMO_APPLICANTS = [
    {
        'username': 'demo_maya',
        'first_name': 'Maya',
        'last_name': 'Chen',
        'email': 'maya@example.com',
        'location': 'Midtown Atlanta, GA',
        'latitude': 33.7810,
        'longitude': -84.3880,
        'skills': ['Python', 'Django', 'Git'],
        'applications': ['Junior Software Engineer', 'Data Analyst'],
        'note': 'I enjoy building clear, reliable tools and collaborating with small product teams.',
    },
    {
        'username': 'demo_jordan',
        'first_name': 'Jordan',
        'last_name': 'Brooks',
        'email': 'jordan@example.com',
        'location': 'Midtown Atlanta, GA',
        'latitude': 33.7830,
        'longitude': -84.3860,
        'skills': ['Communication', 'Project Management', 'Excel'],
        'applications': ['Product Coordinator', 'Operations Analyst'],
        'note': 'My internship experience taught me how to keep cross-functional work organized and moving.',
    },
    {
        'username': 'demo_avery',
        'first_name': 'Avery',
        'last_name': 'Patel',
        'email': 'avery@example.com',
        'location': 'Decatur, GA',
        'latitude': 33.7748,
        'longitude': -84.2963,
        'skills': ['Figma', 'User Research', 'HTML'],
        'applications': ['UX Designer', 'Frontend Developer'],
        'note': 'I care about accessible interfaces and turning research findings into practical designs.',
    },
    {
        'username': 'demo_sam',
        'first_name': 'Sam',
        'last_name': 'Rivera',
        'email': 'sam@example.com',
        'location': 'Decatur, GA',
        'latitude': 33.7760,
        'longitude': -84.2940,
        'skills': ['JavaScript', 'HTML', 'CSS'],
        'applications': ['Frontend Developer'],
        'note': 'I have built responsive interfaces for student organizations and local nonprofits.',
    },
    {
        'username': 'demo_taylor',
        'first_name': 'Taylor',
        'last_name': 'Morgan',
        'email': 'taylor@example.com',
        'location': 'Buckhead Atlanta, GA',
        'latitude': 33.8480,
        'longitude': -84.3700,
        'skills': ['Python', 'SQL', 'Data Analysis'],
        'applications': ['Data Analyst', 'QA Analyst'],
        'note': 'I like finding the story behind a dataset and explaining it in a way teams can act on.',
    },
    {
        'username': 'demo_casey',
        'first_name': 'Casey',
        'last_name': 'Nguyen',
        'email': 'casey@example.com',
        'location': 'Marietta, GA',
        'latitude': 33.9526,
        'longitude': -84.5499,
        'skills': ['Communication', 'Python', 'Testing'],
        'applications': ['Support Engineer', 'QA Analyst'],
        'note': 'I bring a patient support mindset along with hands-on technical troubleshooting experience.',
    },
]

DEMO_STAGES = {
    ('demo_maya', 'Junior Software Engineer'): JobApplication.Status.TECH_INTERVIEW,
    ('demo_maya', 'Data Analyst'): JobApplication.Status.REVIEWING,
    ('demo_jordan', 'Product Coordinator'): JobApplication.Status.BEHAVIORAL_INTERVIEW,
    ('demo_avery', 'UX Designer'): JobApplication.Status.OFFER,
    ('demo_avery', 'Frontend Developer'): JobApplication.Status.SHORTLISTED,
    ('demo_sam', 'Frontend Developer'): JobApplication.Status.HIRED,
    ('demo_taylor', 'QA Analyst'): JobApplication.Status.NOT_SELECTED,
}

DEMO_MESSAGES = [
    ('recruiter', 'Hi Maya, thanks for applying to the Junior Software Engineer role. '
                  'Are you available for a technical interview next week?'),
    ('job_seeker', 'Hi! Yes, I would love to. Tuesday or Wednesday afternoon works best for me.'),
    ('recruiter', 'Great, I will send over a Wednesday 2 PM slot shortly.'),
]


class Command(BaseCommand):
    help = 'Create reusable Scoutly demo jobs and applications.'

    def handle(self, *args, **options):
        recruiter = User.objects.filter(
            username__in=['scoutly_demo_recruiter', 'pathway_demo_recruiter']
        ).first()
        recruiter_created = recruiter is None
        if recruiter_created:
            recruiter = User.objects.create(
                username='scoutly_demo_recruiter',
                role=User.Role.RECRUITER,
            )
        elif recruiter.username == 'pathway_demo_recruiter':
            recruiter.username = 'scoutly_demo_recruiter'
            recruiter.save(update_fields=['username'])
        recruiter.set_password(DEMO_PASSWORD)
        recruiter.save(update_fields=['password'])

        created_count = 0
        updated_count = 0
        jobs_by_title = {}
        for job_data in DEMO_JOBS:
            skill_names = job_data['skills']
            job, created = JobPosting.objects.update_or_create(
                title=job_data['title'],
                company_name=job_data['company_name'],
                posted_by=recruiter,
                defaults={
                    'location': job_data['location'],
                    'latitude': job_data['latitude'],
                    'longitude': job_data['longitude'],
                },
            )
            skills = [Skill.objects.get_or_create(name=name)[0] for name in skill_names]
            job.skills_required.set(skills)
            jobs_by_title[job.title] = job
            created_count += int(created)
            updated_count += int(not created)

        application_count = 0
        for applicant_data in DEMO_APPLICANTS:
            user, _ = User.objects.update_or_create(
                username=applicant_data['username'],
                defaults={
                    'first_name': applicant_data['first_name'],
                    'last_name': applicant_data['last_name'],
                    'email': applicant_data['email'],
                    'role': User.Role.JOB_SEEKER,
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=['password'])
            profile, _ = JobSeekerProfile.objects.update_or_create(
                user=user,
                defaults={
                    'location': applicant_data['location'],
                    'preferred_latitude': applicant_data['latitude'],
                    'preferred_longitude': applicant_data['longitude'],
                    'commute_radius_miles': 25,
                },
            )
            skills = [
                Skill.objects.get_or_create(name=name)[0]
                for name in applicant_data['skills']
            ]
            profile.skills.set(skills)
            for job_title in applicant_data['applications']:
                JobApplication.objects.update_or_create(
                    job=jobs_by_title[job_title],
                    applicant=profile,
                    defaults={
                        'cover_note': applicant_data['note'],
                        'status': DEMO_STAGES.get(
                            (user.username, job_title),
                            JobApplication.Status.SUBMITTED,
                        ),
                    },
                )
                application_count += 1

        maya = User.objects.get(username='demo_maya')
        conversation, created = Conversation.objects.get_or_create(
            recruiter=recruiter,
            job_seeker=maya,
            defaults={'job': jobs_by_title['Junior Software Engineer']},
        )
        if created:
            for sender_role, body in DEMO_MESSAGES:
                sender = recruiter if sender_role == 'recruiter' else maya
                Message.objects.create(conversation=conversation, sender=sender, body=body)

        self.stdout.write(self.style.SUCCESS(
            f'Demo data ready: {created_count} jobs created, '
            f'{updated_count} jobs updated, {application_count} applications ready.'
        ))
        self.stdout.write(
            f'Recruiter login: scoutly_demo_recruiter / {DEMO_PASSWORD}'
        )
