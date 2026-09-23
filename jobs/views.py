from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import JobPosting
from django.http import HttpResponseForbidden
from accounts.models import User

@login_required
def recommended_candidates(request, job_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view this page.")
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    template_data = {}
    template_data['title'] = 'Recommended Candidates'
    template_data['job'] = job
    template_data['candidates'] = job.recommended_candidates()
    return render(request, 'jobs/recommended_candidates.html', {'template_data': template_data})
