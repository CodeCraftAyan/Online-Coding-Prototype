from django.contrib import admin
from .models import Card, Contest, ContestRegistration, ContestProblem, ContestTestCase, ContestSubmission, SubmissionTestCase, Leaderboard, UserCard, SiteSetting

# Register your models here.
admin.site.register(Card)
admin.site.register(Contest)
admin.site.register(ContestRegistration)
admin.site.register(ContestProblem)
admin.site.register(ContestTestCase)
admin.site.register(ContestSubmission)
admin.site.register(SubmissionTestCase)
admin.site.register(Leaderboard)
admin.site.register(UserCard)
admin.site.register(SiteSetting)