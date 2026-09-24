from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.forms import CommutePreferenceForm
from accounts.models import JobSeekerProfile, User
from .models import JobPosting


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
    })


@login_required
def cart(request):
    profile = _job_seeker_profile(request)
    if profile is None:
        return HttpResponseForbidden('Only job seekers have a job cart.')

    jobs = list(profile.cart_jobs.prefetch_related('skills_required'))
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
        'job_postings': JobPosting.objects.filter(posted_by=request.user),
    })
