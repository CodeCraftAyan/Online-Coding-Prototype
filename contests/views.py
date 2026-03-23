from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .judge import judge_submission
from .models import SubmissionTestCase, SiteSetting, Leaderboard
from code_evaluation.models import Submission, RatingHistory
from django.http import JsonResponse

from .models import (
    Contest,
    ContestRegistration,
    ContestProblem,
    ContestSubmission
)


def contest_list(request):
    now = timezone.now()

    upcoming_contests = Contest.objects.filter(end_time__gte=now).order_by("start_time")
    past_contests = Contest.objects.filter(end_time__lt=now).order_by("-start_time")

    context = {
        "upcoming_contests": upcoming_contests,
        "past_contests": past_contests,
        "now": now,
    }

    return render(request, "contests/contests.html", context)


@login_required
def contest_register(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    now = timezone.now()

    if now >= contest.start_time:
        messages.error(request, "Registration is closed. Contest already started.")
        return redirect("contest_list")

    # check already registered
    already_registered = ContestRegistration.objects.filter(
        user=request.user, contest=contest
    ).exists()

    if request.method == "POST":
        if already_registered:
            messages.warning(request, "You are already registered!")
            return redirect("contest", contest_id=contest.id)
        
        unrated = request.POST.get("unrated") == "on"

        ContestRegistration.objects.create(
            user=request.user,
            contest=contest,
            unrated=unrated
        )

        messages.success(request, "Successfully registered!")
        return redirect("contest", contest_id=contest.id)

    context = {
        "contest": contest,
        "already_registered": already_registered,
    }

    return render(request, "contests/contest_register.html", context)


@login_required
def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    now = timezone.now()

    if now < contest.start_time:
        messages.error(request, "Contest has not started yet!")
        return redirect("contest_list")
    
    if now > contest.end_time:
        return redirect("leaderboard", contest_id=contest.id)

    # check registration
    is_registered = ContestRegistration.objects.filter(
        user=request.user, contest=contest
    ).exists()

    if not is_registered:
        messages.error(request, "You must register first!")
        return redirect("contest_register", contest_id=contest.id)

    problems = contest.problems.all()

    context = {
        "contest": contest,
        "problems": problems,
    }

    return render(request, "contests/contest.html", context)


@login_required
def contest_problem(request, contest_id, problem_code):
    contest = get_object_or_404(Contest, id=contest_id)
    problem = get_object_or_404(
        ContestProblem,
        contest=contest,
        code=problem_code
    )

    now = timezone.now()

    if not (contest.start_time <= now <= contest.end_time):
        messages.error(request, "Contest is not live!")
        return redirect("contest_list")

    if request.method == "POST":
        language = request.POST.get("language")
        code = request.POST.get("code")

        submission = ContestSubmission.objects.create(
            user=request.user,
            contest=contest,
            problem=problem,
            language=language,
            code=code,
            status="PENDING"
        )

        messages.success(request, "Submission received!")

        judge_submission(submission)

        submission.refresh_from_db()

        update_leaderboard_entry(submission)
        update_leaderboard(submission.contest)

        return redirect(
            "contest_submission_detail",
            submission_id=submission.id
        )

    context = {
        "contest": contest,
        "problem": problem,
    }

    return render(request, "contests/contest_problem.html", context)


@login_required
def contest_submissions(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    contest_submissions = ContestSubmission.objects.filter(
        contest=contest,
        user=request.user
    )

    normal_submissions = Submission.objects.filter(
        user=request.user
    )

    submissions = list(contest_submissions) + list(normal_submissions)

    submissions.sort(key=lambda x: x.submitted_at, reverse=True)

    context = {
        "contest": contest,
        "submissions": submissions,
    }

    return render(request, "contests/submissions.html", context)


@login_required
def contest_submission_detail(request, submission_id):
    submission = get_object_or_404(
        ContestSubmission,
        id=submission_id,
        user=request.user
    )

    testcase_results = SubmissionTestCase.objects.filter(
        submission=submission
    ).select_related("testcase")

    context = {
        "submission": submission,
        "testcase_results": testcase_results,
    }

    return render(request, "contests/submission_detail.html", context)



def index(request):
    setting, _ = SiteSetting.objects.get_or_create(id=1)

    if request.GET.get("check_video"):
        return JsonResponse({
            "video_triggered_at": setting.video_triggered_at.timestamp() if setting.video_triggered_at else 0
        })

    return render(request, "index.html", {
        "show_video": setting.show_video,
        "video_triggered_at": setting.video_triggered_at.timestamp() if setting.video_triggered_at else 0
    })

def video_status(request):
    setting, _ = SiteSetting.objects.get_or_create(id=1)

    return JsonResponse({
        "show_video": setting.show_video,
        "video_triggered_at": setting.video_triggered_at.timestamp() if setting.video_triggered_at else 0
    })



def update_leaderboard(contest):
    entries = Leaderboard.objects.filter(contest=contest).order_by('-solved', 'penalty')

    for i, entry in enumerate(entries, start=1):
        entry.rank = i
        entry.save()


def update_leaderboard_entry(submission):
    # Only count Accepted submissions
    if submission.verdict != "AC":
        return

    entry, _ = Leaderboard.objects.get_or_create(
        contest=submission.contest,
        user=submission.user
    )

    # Check if already solved this problem before
    already_solved = ContestSubmission.objects.filter(
        contest=submission.contest,
        user=submission.user,
        problem=submission.problem,
        verdict="AC"
    ).exclude(id=submission.id).exists()

    if not already_solved:
        entry.solved += 1

        # simple penalty (minutes from contest start)
        time_taken = int(
            (submission.submitted_at - submission.contest.start_time).total_seconds() // 60
        )
        entry.penalty += time_taken

        entry.save()


def leaderboard(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    update_leaderboard(contest)

    if contest.end_time < timezone.now():
        update_ratings(contest)

    leaderboard_qs = Leaderboard.objects.filter(contest=contest).select_related("user")

    context = {
        "contest": contest,
        "leaderboard": leaderboard_qs
    }

    return render(request, 'contests/leaderboard.html', context)


def update_ratings(contest):
    entries = Leaderboard.objects.filter(contest=contest).order_by('rank')

    for entry in entries:
        profile = entry.user.profile

        # prevent duplicate rating entries
        already_exists = RatingHistory.objects.filter(
            user=entry.user,
            contest=contest
        ).exists()

        if already_exists:
            continue

        delta = max(0, 50 - entry.rank * 2)
        profile.rating += delta
        profile.save()

        RatingHistory.objects.create(
            user=entry.user,
            contest=contest,
            rating=profile.rating
        )