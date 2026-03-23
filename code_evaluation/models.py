from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from contests.models import Contest

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    display_name = models.CharField(max_length=250)

    rating = models.IntegerField(default=0)
    solved_count = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    country = models.CharField(max_length=50, blank=True)
    profile_image = models.URLField(blank=True, null=True)
    
    last_seen = models.DateTimeField(default=timezone.now)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class RatingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)

    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.rating}"


class Problem(models.Model):
    problem_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    input_description = models.TextField()
    output_description = models.TextField()
    constraints = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('Easy', 'Easy'),
            ('Medium', 'Medium'),
            ('Hard', 'Hard'),
        ]
    )
    time_limit = models.FloatField(default=1.0)
    memory_limit = models.IntegerField(default=256)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)

    # need to add image field also for question

    def __str__(self):
        return f"{self.problem_id} - {self.title}"


class Submission(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('RE', 'Runtime Error'),
        ('CE', 'Compilation Error'),
    ]

    LANGUAGE_CHOICES = [
        ('python', 'Python 3'),
        ('cpp', 'GNU C++20'),
        ('c', 'GNU C11'),
        ('java', 'Java 21'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)
    code = models.TextField()

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')

    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.IntegerField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.problem.problem_id}"


class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    input_data = models.TextField()
    output_data = models.TextField()

    is_sample = models.BooleanField(default=False)


class SubmissionTestCase(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE)

    user_output = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)

    status = models.CharField(max_length=20)

    execution_time = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.submission.id} - Testcase {self.testcase.id}"