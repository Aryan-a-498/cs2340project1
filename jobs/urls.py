from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_job_postings, name='jobs.my_job_postings'),
    path('explore/', views.explore, name='jobs.explore'),
    path('cart/', views.cart, name='jobs.cart'),
    path('<int:job_id>/cart/add/', views.add_to_cart, name='jobs.add_to_cart'),
    path('<int:job_id>/cart/remove/', views.remove_from_cart, name='jobs.remove_from_cart'),
    path('<int:job_id>/candidates/', views.recommended_candidates, name='jobs.recommended_candidates'),
]
