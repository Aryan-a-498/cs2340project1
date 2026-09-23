from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_job_postings, name='jobs.my_job_postings'),
    path('<int:job_id>/candidates/', views.recommended_candidates, name='jobs.recommended_candidates'),
]
