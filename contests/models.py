from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Create your models here.
class Card(models.Model):
    SUIT_CHOICES = [
        ("hearts", "Hearts"),
        ("spades", "Spades"),
        ("diamonds", "Diamonds"),
        ("clubs", "Clubs"),
        ("joker", "Joker"),
    ]

    RANK_CHOICES = [
        ("A", "Ace"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6"),
        ("7", "7"),
        ("8", "8"),
        ("9", "9"),
        ("10", "10"),
        ("J", "Jack"),
        ("Q", "Queen"),
        ("K", "King"),
        ("JOKER", "Joker"),
    ]

    suit = models.CharField(max_length=10, choices=SUIT_CHOICES)
    rank = models.CharField(max_length=10, choices=RANK_CHOICES)

    image = models.URLField()
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('rank', 'suit')

    def save(self, *args, **kwargs):
        if self.suit == "joker":
            self.rank = "JOKER"
        elif self.rank == "JOKER":
            raise ValueError("Only joker suit can have JOKER rank")
        super().save(*args, **kwargs)

    def __str__(self):
        if self.suit == "joker":
            return "Joker"
        return f"{self.get_rank_display()} of {self.get_suit_display()}"



class Contest(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")

    card = models.ForeignKey(Card, on_delete=models.CASCADE)

    description = models.TextField(blank=True)

    def __str__(self):
        return self.title



class ContestRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="registrations")

    unrated = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('user', 'contest')

    def __str__(self):
        return f"{self.user} -> {self.contest}"



class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="problems")

    code = models.CharField(max_length=5)
    title = models.CharField(max_length=200)

    time_limit = models.FloatField(default=2.0)
    memory_limit = models.IntegerField(default=256)

    statement = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()

    solved_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'code')

    def __str__(self):
        return f"{self.code}. {self.title}"



class ContestTestCase(models.Model):
    problem = models.ForeignKey(ContestProblem, on_delete=models.CASCADE, related_name="testcases")

    input_data = models.TextField()
    expected_output = models.TextField()

    is_sample = models.BooleanField(default=False)

    def __str__(self):
        return f"Testcase for {self.problem}"



class ContestSubmission(models.Model):
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
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(ContestProblem, on_delete=models.CASCADE)

    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)
    code = models.TextField()

    verdict = models.CharField(max_length=10, choices=STATUS_CHOICES, default="WA")

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')

    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.IntegerField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user} - {self.problem} - {self.verdict}"



class SubmissionTestCase(models.Model):
    submission = models.ForeignKey(ContestSubmission, on_delete=models.CASCADE)
    testcase = models.ForeignKey(ContestTestCase, on_delete=models.CASCADE)

    user_output = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=ContestSubmission.STATUS_CHOICES)

    execution_time = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.submission.id} - Testcase {self.testcase.id}"



class Leaderboard(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="leaderboard")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    solved = models.IntegerField(default=0)
    penalty = models.IntegerField(default=0)

    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('contest', 'user')
        ordering = ['-solved', 'penalty']

    def __str__(self):
        return f"{self.user} - {self.contest}"



class UserCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="earned_cards")

    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'card', 'contest')

    def __str__(self):
        return f"{self.user} collected {self.card}"




class SiteSetting(models.Model):
    show_video = models.BooleanField(default=False)
    video_triggered_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        trigger = False

        if self.pk:
            old = SiteSetting.objects.get(pk=self.pk)
            if not old.show_video and self.show_video:
                self.video_triggered_at = timezone.now()
                trigger = True
        else:
            if self.show_video:
                self.video_triggered_at = timezone.now()
                trigger = True

        super().save(*args, **kwargs)

        # SEND WEBSOCKET EVENT
        if trigger:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "video_group",
                {
                    "type": "send_video_trigger",
                    "video_triggered_at": self.video_triggered_at.timestamp()
                }
            )