from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.forms import CommutePreferenceForm
from accounts.models import JobSeekerProfile, User
from .forms import ApplicationStatusForm, JobApplicationForm
from .models import JobApplication, JobPosting


APPLICANT_CLUSTER_SIZE = 0.05


def _job_seeker_profile(request):
    if request.user.role != User.Role.JOB_SEEKER:
        return None
    # get_or_create also supports job seekers created before profiles were added.
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    return profile


def _nearby_jobs(profile):
    if profile.preferred_latitude is None or profile.preferred_longitude is None:
        return []

    nearby_jobs = []
    jobs = JobPosting.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    ).prefetch_related('skills_required')
    for job in jobs:
        distance = job.distance_from(
            profile.preferred_latitude,
            profile.preferred_longitude,
        )
        if distance <= profile.commute_radius_miles:
            job.distance_miles = distance
            nearby_jobs.append(job)
    return sorted(nearby_jobs, key=lambda job: job.distance_miles)


def _display_name(user):
    return user.get_full_name() or user.username


@login_required
@require_http_methods(['GET', 'POST'])
def explore(request):
    profile = _job_seeker_profile(request)
    if profile is None:
        return HttpResponseForbidden('Only job seekers can explore jobs.')

    if request.method == 'POST':
        form = CommutePreferenceForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your commute preference was updated.')
            return redirect('jobs.explore')
    else:
        form = CommutePreferenceForm(instance=profile)

    nearby_jobs = _nearby_jobs(profile)
    cart_job_ids = set(profile.cart_jobs.values_list('id', flat=True))
    applied_job_ids = set(profile.applications.values_list('job_id', flat=True))
    map_jobs = [
        {
            'id': job.id,
            'title': job.title,
            'company': job.company_name,
            'latitude': job.latitude,
            'longitude': job.longitude,
            'distance': round(job.distance_miles, 1),
        }
        for job in nearby_jobs
    ]
    return render(request, 'jobs/explore.html', {
        'title': 'Explore Jobs',
        'profile': profile,
        'form': form,
        'jobs': nearby_jobs,
        'map_jobs': map_jobs,
        'cart_job_ids': cart_job_ids,
        'applied_job_ids': applied_job_ids,
    })


@login_required
def cart(request):
    profile = _job_seeker_profile(request)
    if profile is None:
        return HttpResponseForbidden('Only job seekers have a job cart.')

    jobs = list(profile.cart_jobs.prefetch_related('skills_required'))
    applied_job_ids = set(profile.applications.values_list('job_id', flat=True))
    for job in jobs:
        job.distance_miles = None
        if profile.preferred_latitude is not None and profile.preferred_longitude is not None:
            job.distance_miles = job.distance_from(
                profile.preferred_latitude,
                profile.preferred_longitude,
            )
    return render(request, 'jobs/cart.html', {
        'title': 'Job Cart',
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def apply_to_job(request, job_id):
    profile = _job_seeker_profile(request)
    if profile is None:
        return HttpResponseForbidden('Only job seekers can apply to jobs.')
    job = get_object_or_404(
        JobPosting.objects.prefetch_related('skills_required'),
        id=job_id,
    )
    if JobApplication.objects.filter(job=job, applicant=profile).exists():
        messages.info(request, 'You already applied to this job.')
        return redirect('jobs.explore')

    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = profile
            application.save()
            messages.success(request, f'Your application to {job.title} was submitted.')
            return redirect('jobs.explore')
    else:
        form = JobApplicationForm()

    return render(request, 'jobs/apply.html', {
        'title': f'Apply to {job.title}',
        'job': job,
        'profile': profile,
        'form': form,
    })


@login_required
@require_POST
def add_to_cart(request, job_id):
    profile = _job_seeker_profile(request)
    if profile is None:
        return HttpResponseForbidden('Only job seekers have a job cart.')
    job = get_object_or_404(JobPosting, id=job_id)
    profile.cart_jobs.add(job)
    messages.success(request, f'{job.title} was added to your cart.')
    return redirect('jobs.explore')


@login_required
@require_POST
def remove_from_cart(request, job_id):
    profile = _job_seeker_profile(request)
    if profile is None:
        return HttpResponseForbidden('Only job seekers have a job cart.')
    job = get_object_or_404(JobPosting, id=job_id)
    profile.cart_jobs.remove(job)
    messages.success(request, f'{job.title} was removed from your cart.')
    return redirect('jobs.cart')


@login_required
def job_applications(request, job_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden('Only recruiters can review applications.')
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    applications = job.applications.select_related(
        'applicant__user'
    ).prefetch_related('applicant__skills')
    return render(request, 'jobs/job_applications.html', {
        'title': f'Applicants for {job.title}',
        'job': job,
        'applications': applications,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def application_detail(request, job_id, application_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden('Only recruiters can review applications.')
    application = get_object_or_404(
        JobApplication.objects.select_related(
            'job', 'applicant__user'
        ).prefetch_related('job__skills_required', 'applicant__skills'),
        id=application_id,
        job_id=job_id,
        job__posted_by=request.user,
    )

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application status updated.')
            return redirect(
                'jobs.application_detail',
                job_id=job_id,
                application_id=application_id,
            )
    else:
        form = ApplicationStatusForm(instance=application)

    candidate_skills = list(application.applicant.skills.all())
    required_skills = list(application.job.skills_required.all())
    candidate_skill_names = {skill.name for skill in candidate_skills}
    matched_skills = [
        skill for skill in required_skills if skill.name in candidate_skill_names
    ]

    return render(request, 'jobs/application_detail.html', {
        'title': f'Application from {_display_name(application.applicant.user)}',
        'application': application,
        'candidate': application.applicant,
        'candidate_name': _display_name(application.applicant.user),
        'candidate_skills': candidate_skills,
        'required_skills': required_skills,
        'matched_skills': matched_skills,
        'status_form': form,
    })


@login_required
def pipeline(request, job_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden('Only recruiters can manage hiring pipelines.')
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    applications = job.applications.select_related(
        'applicant__user'
    ).prefetch_related('applicant__skills').order_by('status_changed_at')

    columns = {
        status: {'status': status, 'label': label, 'applications': []}
        for status, label in JobApplication.Status.choices
    }
    for application in applications:
        columns[application.status]['applications'].append(application)

    return render(request, 'jobs/pipeline.html', {
        'title': f'Pipeline for {job.title}',
        'job': job,
        'columns': list(columns.values()),
        'status_choices': JobApplication.Status.choices,
        'application_count': len(applications),
    })


@login_required
@require_POST
def pipeline_move(request, job_id, application_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden('Only recruiters can manage hiring pipelines.')
    application = get_object_or_404(
        JobApplication.objects.select_related('applicant__user'),
        id=application_id,
        job_id=job_id,
        job__posted_by=request.user,
    )
    status = request.POST.get('status')
    if status not in JobApplication.Status.values:
        return HttpResponseBadRequest('Choose a valid hiring stage.')

    application.move_to(status)
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'status': application.status,
            'label': application.get_status_display(),
        })

    messages.success(
        request,
        f'{_display_name(application.applicant.user)} moved to '
        f'{application.get_status_display()}.',
    )
    return redirect('jobs.pipeline', job_id=job_id)


@login_required
def applicant_map(request):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden('Only recruiters can view applicant locations.')

    recruiter_jobs = request.user.job_postings.order_by('title')
    applications = JobApplication.objects.filter(
        job__posted_by=request.user
    ).select_related('job', 'applicant__user')

    selected_job = None
    if request.GET.get('job'):
        selected_job = get_object_or_404(recruiter_jobs, id=request.GET['job'])
        applications = applications.filter(job=selected_job)

    applications = list(applications)
    applicants = {}
    for application in applications:
        entry = applicants.setdefault(application.applicant_id, {
            'profile': application.applicant,
            'applications': [],
        })
        entry['applications'].append(application)

    grouped_clusters = {}
    located_applicants = 0
    for entry in applicants.values():
        profile = entry['profile']
        if profile.preferred_latitude is None or profile.preferred_longitude is None:
            continue
        located_applicants += 1
        cluster_key = (
            round(profile.preferred_latitude / APPLICANT_CLUSTER_SIZE),
            round(profile.preferred_longitude / APPLICANT_CLUSTER_SIZE),
        )
        grouped_clusters.setdefault(cluster_key, []).append(entry)

    clusters = []
    for (latitude_key, longitude_key), entries in grouped_clusters.items():
        cluster_applicants = []
        for entry in entries:
            profile = entry['profile']
            application = entry['applications'][0]
            cluster_applicants.append({
                'name': _display_name(profile.user),
                'location': profile.location or 'Location not labeled',
                'url': reverse(
                    'jobs.application_detail',
                    args=[application.job_id, application.id],
                ),
            })
        clusters.append({
            'latitude': latitude_key * APPLICANT_CLUSTER_SIZE,
            'longitude': longitude_key * APPLICANT_CLUSTER_SIZE,
            'count': len(entries),
            'applicants': cluster_applicants,
        })

    return render(request, 'jobs/applicant_map.html', {
        'title': 'Applicant Map',
        'recruiter_jobs': recruiter_jobs,
        'selected_job': selected_job,
        'applications': applications,
        'clusters': clusters,
        'applicant_count': len(applicants),
        'located_applicant_count': located_applicants,
    })


@login_required
def recommended_candidates(request, job_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view this page.")
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    return render(request, 'jobs/recommended_candidates.html', {
        'title': 'Recommended Candidates',
        'job': job,
        'candidates': job.recommended_candidates(),
    })


@login_required
def my_job_postings(request):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view this page.")
    return render(request, 'jobs/my_job_postings.html', {
        'title': 'My Job Postings',
        'job_postings': JobPosting.objects.filter(
            posted_by=request.user
        ).annotate(application_count=Count('applications')),
    })
