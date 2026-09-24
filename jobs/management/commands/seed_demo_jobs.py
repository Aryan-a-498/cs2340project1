from django.core.management.base import BaseCommand

from accounts.models import User
from jobs.models import JobPosting, Skill


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


class Command(BaseCommand):
    help = 'Create reusable Atlanta-area demo jobs for local development.'

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
        if recruiter_created:
            recruiter.set_unusable_password()
            recruiter.save(update_fields=['password'])

        created_count = 0
        updated_count = 0
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
            created_count += int(created)
            updated_count += int(not created)

        self.stdout.write(self.style.SUCCESS(
            f'Demo jobs ready: {created_count} created, {updated_count} updated.'
        ))
