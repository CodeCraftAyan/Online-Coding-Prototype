from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('problems/', views.home, name='home'),
    path('problem/<str:problem_id>/', views.problem, name='problem'),
    path("submission/<int:submission_id>/", views.submission_detail, name="submission_detail"),
    path("submissions/", views.my_submissions, name="submissions"),
    path('profile/<str:user_id>/', views.user_profile, name='profile'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('create_problem/', views.create_problem, name='create_problem'),
]