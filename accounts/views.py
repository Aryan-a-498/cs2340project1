from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CustomUserCreationForm
from .models import JobSeekerProfile, User


@require_http_methods(['GET', 'POST'])
def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == User.Role.JOB_SEEKER:
                JobSeekerProfile.objects.create(user=user)
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})


@require_http_methods(['GET', 'POST'])
def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password'],
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html', {'template_data': template_data})
        else:
            auth_login(request, user)
            if user.role == User.Role.JOB_SEEKER:
                JobSeekerProfile.objects.get_or_create(user=user)
                return redirect('jobs.explore')
            return redirect('jobs.my_job_postings')


@require_POST
def logout(request):
    auth_logout(request)
    return redirect('accounts.login')
