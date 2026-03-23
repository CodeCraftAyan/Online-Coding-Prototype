from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Problem, Profile, Submission, SubmissionTestCase, RatingHistory
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from datetime import timedelta
from .judge import judge_submission
import threading
from django.db.models import Count
from contests.models import ContestSubmission
from django.db.models import Count, Q
from contests.models import ContestSubmission, UserCard, ContestRegistration, Leaderboard, Contest, ContestProblem


# Create your views here.
def index(request):
    return render(request, 'index.html')

def home(request):
    problems = Problem.objects.all()
    return render(request, 'problems/problem_list.html', {'problems' : problems})

def problem(request, problem_id):
    problem = get_object_or_404(Problem, problem_id=problem_id)

    if request.method == "POST":
        language = request.POST.get("language")
        code = request.POST.get("code")

        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=language,
            code=code,
            status="PENDING"
        )

        thread = threading.Thread(target=judge_submission, args=(submission,))
        thread.start()

        return redirect("submission_detail", submission_id=submission.id)

    return render(request, 'problems/problem.html', {'problem': problem})


def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    testcase_results = SubmissionTestCase.objects.filter(
        submission=submission
    )

    return render(request, "problems/submission.html", {
        "submission": submission,
        "testcase_results": testcase_results
    })


def my_submissions(request):
    practice_submissions = Submission.objects.filter(
        user=request.user
    )

    contest_submissions = ContestSubmission.objects.filter(
        user=request.user
    )

    # merge both
    submissions = list(practice_submissions) + list(contest_submissions)

    # sort by latest
    submissions.sort(key=lambda x: x.submitted_at, reverse=True)

    return render(request, "problems/submissions.html", {
        "submissions": submissions
    })


def create_problem(request):
    return render(request, 'problems/add_problem.html')


def user_profile(request, user_id):
    profile = get_object_or_404(Profile, user__username=user_id)
    user = profile.user

    online = timezone.now() - profile.last_seen < timedelta(minutes=5)

    # Global Rank
    rank = Profile.objects.filter(rating__gt=profile.rating).count() + 1

    # Solved Problems (Practice)
    solved_problems = Submission.objects.filter(
        user=user,
        status="AC"
    ).values("problem").distinct()

    solved_count = solved_problems.count()

    # Contest solved
    contest_solved = ContestSubmission.objects.filter(
        user=user,
        verdict="AC"
    ).values("problem").distinct().count()

    # Total points system
    points = solved_count * 10 + contest_solved * 20

    # Update profile automatically
    if profile.solved_count != solved_count or profile.points != points:
        profile.solved_count = solved_count
        profile.points = points
        profile.save(update_fields=["solved_count", "points"])

    # Recent activity
    practice = Submission.objects.filter(user=user).select_related("problem")
    contest_subs = ContestSubmission.objects.filter(user=user).select_related("problem")

    recent_activity = sorted(
        list(practice) + list(contest_subs),
        key=lambda x: x.submitted_at,
        reverse=True
    )[:10]

    # Submission statistics
    submissions = Submission.objects.filter(user=user)

    ac_count = submissions.filter(status="AC").count()
    wa_count = submissions.filter(status="WA").count()
    tle_count = submissions.filter(status="TLE").count()

    # Cards collected
    cards = UserCard.objects.filter(user=user).select_related("card")[:20]

    # Contest participated
    now = timezone.now()

    contests = ContestRegistration.objects.filter(
        user=user,
        contest__end_time__gt=now
    ).select_related("contest").order_by("contest__start_time")[:5]

    # mark state
    for c in contests:
        if c.contest.start_time <= now <= c.contest.end_time:
            c.status = "LIVE"
        elif now < c.contest.start_time:
            c.status = "UPCOMING"
        else:
            c.status = "ENDED"

    rating_history = RatingHistory.objects.filter(user=user).order_by("created_at")

    rating_data = RatingHistory.objects.filter(user=user).order_by("created_at")

    rating_points = [r.rating for r in rating_data]
    rating_labels = [r.contest.title for r in rating_data]

    peak_rating = max(rating_points) if rating_points else profile.rating

    # contest stats
    contest_played = ContestRegistration.objects.filter(user=user).count()

    best_rank = Leaderboard.objects.filter(user=user).order_by("rank").first()
    best_rank = best_rank.rank if best_rank else None

    today = timezone.now().date()
    start_date = today - timedelta(days=364)

    practice = Submission.objects.filter(
        user=user,
        submitted_at__date__gte=start_date
    )

    contest = ContestSubmission.objects.filter(
        user=user,
        submitted_at__date__gte=start_date
    )

    all_subs = list(practice) + list(contest)

    activity_dict = {}

    for sub in all_subs:
        day = sub.submitted_at.date()
        activity_dict[day] = activity_dict.get(day, 0) + 1

    activity_data = []
    for i in range(365):
        d = start_date + timedelta(days=i)
        count = activity_dict.get(d, 0)
        activity_data.append(count)
    
    #earned 
    earned_cards = []

    contests_all = Contest.objects.all()

    for contest_obj in contests_all:
        total_problems = ContestProblem.objects.filter(contest=contest_obj).count()

        solved = ContestSubmission.objects.filter(
            user=user,
            contest=contest_obj,
            verdict="AC"
        ).values("problem").distinct().count()

        if total_problems > 0 and solved == total_problems:
            earned_cards.append(contest_obj.card)
    
    #best card
    best_card = earned_cards[0] if earned_cards else None

    context = {
        "profile_user": profile,
        "online": online,
        "rank": rank,
        "recent_activity": recent_activity,
        "ac_count": ac_count,
        "wa_count": wa_count,
        "tle_count": tle_count,
        "cards": cards,
        "contest_solved": contest_solved,
        "contests": contests,
        "rating_history": rating_history,
        "rating_points": rating_points,
        "rating_labels": rating_labels,
        "peak_rating": peak_rating,
        "contest_played": contest_played,
        "best_rank": best_rank,
        "activity_data": activity_data,
        "earned_cards": earned_cards,
        "best_card": best_card,
    }

    return render(request, "profile.html", context)

def login_register(request):
    return render(request, 'login_register.html')

def register(request):
    if request.method == "POST":
        display_name = request.POST.get("username")
        user_id = request.POST.get("user_id")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=user_id).exists():
            messages.error(request, "User ID already taken")
            return redirect("login")

        user = User.objects.create_user(
            username = user_id,
            email = email,
            password = password
        )

        Profile.objects.create(
            user=user,
            display_name=display_name
        )

        messages.success(request, "Successfully registard!")
        return redirect("login")

def user_login(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")

        user = authenticate(request, username=user_id, password=password)

        if user:
            login(request, user)
            messages.success(request, 'Login sucessfully!!')
            return redirect("index")
        
        if not request.user.is_authenticated:
            messages.warning(request, 'Login required!')
            return redirect("login")

    return render(request, 'login_register.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Logout successfully!!')
    return redirect('index')


# Page Errors
def error_400(request, exception):
    return render(request, "error.html", {
        "code": 400,
        "title": "Malformed Transmission.",
        "message": "Your request was corrupted before reaching the core. Please verify the payload and try again.",
        "sys_status_msg": "invalid_request"
    }, status=400)


def error_403(request, exception):
    return render(request, "error.html", {
        "code": 403,
        "title": "Access Denied.",
        "message": "You do not have the required clearance to access this resource.",
        "sys_status_msg": "forbidden"
    }, status=403)


def error_404(request, exception):
    return render(request, "error.html", {
        "code": 404,
        "title": "Lost in the void.",
        "message": "This coordinate leads to nowhere. The file you are looking for has vanished into the platform's history.",
        "sys_status_msg": "disconnected"
    }, status=404)


def error_405(request, exception):
    return render(request, "error.html", {
        "code": 405,
        "title": "Protocol Violation.",
        "message": "The requested operation is not supported on this endpoint.",
        "sys_status_msg": "method_rejected"
    }, status=405)


def error_408(request, exception):
    return render(request, "error.html", {
        "code": 408,
        "title": "Signal Timeout.",
        "message": "The server waited too long for your request. Transmission window expired.",
        "sys_status_msg": "timeout"
    }, status=408)


def error_429(request, exception):
    return render(request, "error.html", {
        "code": 429,
        "title": "Rate Limit Exceeded.",
        "message": "Too many requests detected. Please slow down and try again shortly.",
        "sys_status_msg": "throttled"
    }, status=429)


def error_500(request):
    return render(request, "error.html", {
        "code": 500,
        "title": "Core System Failure.",
        "message": "An unexpected internal fault occurred. Our engineers have been notified.",
        "sys_status_msg": "critical_error"
    }, status=500)


def error_502(request, exception):
    return render(request, "error.html", {
        "code": 502,
        "title": "Gateway Malfunction.",
        "message": "Upstream service returned an invalid response.",
        "sys_status_msg": "gateway_error"
    }, status=502)


def error_503(request, exception):
    return render(request, "error.html", {
        "code": 503,
        "title": "Service Offline.",
        "message": "The system is temporarily unavailable due to maintenance or overload.",
        "sys_status_msg": "maintenance_mode"
    }, status=503)
