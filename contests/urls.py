from django.urls import path
from . import views

urlpatterns = [
    path("", views.contest_list, name="contest_list"),
    path("<int:contest_id>/", views.contest_detail, name="contest"),
    path("<int:contest_id>/register/", views.contest_register, name="contest_register"),
    path("<int:contest_id>/problem/<str:problem_code>/", views.contest_problem, name="contest_problem"),
    path("<int:contest_id>/submissions/", views.contest_submissions, name="contest_submissions"),
    path("submission/<int:submission_id>/", views.contest_submission_detail, name="contest_submission_detail"),
    path('<int:contest_id>/leaderboard/', views.leaderboard, name='leaderboard'),
]