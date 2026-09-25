from django.urls import path
from . import views

urlpatterns = [
  path('login/', views.login, name='accounts.login'),
  path('logout/', views.logout, name='accounts.logout'),
  path('signup/', views.signup, name='accounts.signup'),
  path('profile/', views.job_seeker_profile, name='accounts.profile'),
]
