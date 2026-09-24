from django.shortcuts import redirect

from accounts.models import User


def home(request):
    if not request.user.is_authenticated:
        return redirect('accounts.login')
    if request.user.role == User.Role.JOB_SEEKER:
        return redirect('jobs.explore')
    return redirect('jobs.my_job_postings')
