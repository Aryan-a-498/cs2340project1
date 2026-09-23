from django.urls import path
from . import views

urlpatterns = [
    path('<int:job_id>/candidates/', views.recommended_candidates, name='jobs.recommended_candidates'),
]
