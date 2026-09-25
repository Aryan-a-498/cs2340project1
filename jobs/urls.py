from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_job_postings, name='jobs.my_job_postings'),
    path('explore/', views.explore, name='jobs.explore'),
    path('cart/', views.cart, name='jobs.cart'),
    path('applicants/map/', views.applicant_map, name='jobs.applicant_map'),
    path('<int:job_id>/apply/', views.apply_to_job, name='jobs.apply'),
    path('<int:job_id>/cart/add/', views.add_to_cart, name='jobs.add_to_cart'),
    path('<int:job_id>/cart/remove/', views.remove_from_cart, name='jobs.remove_from_cart'),
    path('<int:job_id>/applications/', views.job_applications, name='jobs.applications'),
    path(
        '<int:job_id>/applications/<int:application_id>/',
        views.application_detail,
        name='jobs.application_detail',
    ),
    path('<int:job_id>/pipeline/', views.pipeline, name='jobs.pipeline'),
    path(
        '<int:job_id>/pipeline/<int:application_id>/move/',
        views.pipeline_move,
        name='jobs.pipeline_move',
    ),
    path('<int:job_id>/candidates/', views.recommended_candidates, name='jobs.recommended_candidates'),
]
