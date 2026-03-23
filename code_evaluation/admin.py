from django.contrib import admin
from .models import Problem, Profile, Submission, TestCase, SubmissionTestCase

# Register your models here.
admin.site.register(Problem)
admin.site.register(Profile)
admin.site.register(Submission)
admin.site.register(TestCase)
admin.site.register(SubmissionTestCase)