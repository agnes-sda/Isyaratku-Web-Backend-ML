from django.shortcuts import render
from django.http import HttpResponse
from .models import  SignLesson,LessonCategory
from .models import PageVisit, QuizSubmission, CommunityPost, PostComment
import string
import random
# Create your views here.
from django.shortcuts import render, redirect
from .forms import IsyaratkuSignUpForm , ProfileForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .models import QuizModule, Question, QuizSubmission
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg
from datetime import timedelta
from .models import PageVisit, QuizSubmission


# views.py
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout_view(request):
    logout(request)
    return redirect('login') # Redirects back to your login page
class CustomLoginView(LoginView):
    template_name = 'Login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dictionary')  # Change 'dashboard' to your home/dashboard URL name
def mainpage(request):
    return render(request, "mainmenu.html")

@login_required
def home(request):
    words = SignLesson.objects.all()
    categories = LessonCategory.objects.all()
    alphabet = list(string.ascii_uppercase)  # Generates ['A', 'B', 'C', ...]

    # 1. Handle Search Input
    search_query = request.GET.get('search', '')
    if search_query:
        words = words.filter(title__icontains=search_query)

    # 2. Handle Alphabet Filter
    letter_filter = request.GET.get('letter', '')
    if letter_filter and letter_filter != 'All':
        words = words.filter(letter__iexact=letter_filter)

    # 3. Handle Category Filter
    category_filter = request.GET.get('category', '')
    if category_filter and category_filter != 'Common Words':
        words = words.filter(categories__slug=category_filter)

    context = {
        'words': words,
        'categories': categories,
        'alphabet': alphabet,
        'selected_letter': letter_filter or 'All',
        'selected_category': category_filter or 'Common Words',
        'search_query': search_query,
    }
    return render(request,"home.html",context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import QuizModule  # Ensure QuizModule is imported properly

@login_required
def quizzes(request):
    queryset = QuizModule.objects.all()

    search_query = request.GET.get('search', '').strip()
    selected_category = request.GET.get('category', 'All')

    # Apply filters
    if search_query:
        queryset = queryset.filter(title__icontains=search_query)

    if selected_category and selected_category != 'All':
        queryset = queryset.filter(category__slug=selected_category)

    context = {
        'modules': queryset,
        'search_query': search_query,
        'selected_category': selected_category,
        # --- ADD THIS LINE SO THE LOOP HAS DATA ---
        'categories': LessonCategory.objects.all(),
    }

    return render(request, 'Quizziz.html', context)


import random  # Make sure this is at the absolute top of your views.py file
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import QuizModule, QuizSubmission, Profile  # Added Profile and QuizSubmission imports

@login_required
def take_quiz(request, slug):
    module = get_object_or_404(QuizModule, slug=slug)
    questions = list(module.questions.all())

    if request.method == "POST":
        correct_count = 0
        total_questions = len(questions)

        for question in questions:
            user_answer = request.POST.get(f"question_{question.id}")
            if user_answer == question.correct_answer:
                correct_count += 1

        accuracy = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        score_fraction_str = f"{correct_count}/{total_questions}"
        points_earned = correct_count * 10  # Calculate points from this run

        # Save submission history log
        QuizSubmission.objects.create(
            user=request.user,
            module=module,
            score_fraction=score_fraction_str,
            accuracy_percentage=accuracy
        )

        # Update profile points
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.score += points_earned
        profile.save()

        # --- REDIRECT TO THE CONGRATS PAGE WITH URL PARAMETERS ---
        return redirect(
            f'/quizzes/results/?module={module.title}&score={score_fraction_str}&accuracy={accuracy}&points={points_earned}')

    # --- KEEP YOUR RANDOMIZATION FOR GET REQUESTS ---
    for question in questions:
        options_pool = [question.correct_answer, question.option_b, question.option_c, question.option_d]
        question.randomized_choices = random.sample(options_pool, len(options_pool))

    return render(request, 'take_quiz.html', {'module': module, 'questions': questions})
@login_required
def practice(request):
    return render(request,"practice.html")


from datetime import timedelta


from django.shortcuts import render
from django.utils import timezone
@login_required
def progress(request):
    # 1. Initialize safe default fallback states for guests / anonymous users
    weekly_minutes = [0.0] * 7
    user_submissions = []
    total_quizzes_taken = 0
    lifetime_accuracy = 0.0

    # 2. Only run queries if the user is logged in
    if request.user.is_authenticated:
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)

        # Update and check streak data
        update_profile_streak(request.user)
        profile = request.user.profile

        if profile.last_completed_date and profile.last_completed_date < yesterday:
            profile.streak = 0
            profile.save()

        # Calculate weekly activity usage minutes
        start_of_week = today - timedelta(days=today.weekday())
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]

        weekly_minutes = []
        for day in week_days:
            daily_seconds = PageVisit.objects.filter(
                user=request.user,
                created_at__date=day
            ).aggregate(total=Sum('duration_seconds'))['total'] or 0.0

            daily_minutes = round(daily_seconds / 60.0, 1)
            weekly_minutes.append(daily_minutes)

        # --- THE CORRECTED ACCURACY ENGINE ---
        # FIXED: Changed from '-submitted_at' to '-created_at' right here!
        user_submissions = QuizSubmission.objects.filter(user=request.user).order_by('-created_at')

        # Extract total quiz completion logs count
        total_quizzes_taken = user_submissions.count()

        # Compute lifetime average accuracy scores
        average_data = user_submissions.aggregate(Avg('accuracy_percentage'))
        if average_data['accuracy_percentage__avg'] is not None:
            lifetime_accuracy = round(average_data['accuracy_percentage__avg'], 1)

    # 3. Ship all calculated assets back to your UI layout canvas
    context = {
        'weekly_minutes': weekly_minutes,
        'submissions': user_submissions,
        'total_quizzes': total_quizzes_taken,
        'lifetime_accuracy': lifetime_accuracy,
    }
    return render(request, 'progress.html', context)


@login_required
def community(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')
        if action == 'create_comment':
            post_id = request.POST.get('post_id')
            content = request.POST.get('comment_content')
            if post_id and content:
                post = CommunityPost.objects.get(id=post_id)
                comment = PostComment.objects.create(post=post, user=request.user, content=content)
                # Return data for JavaScript to update the page
                return JsonResponse({
                    'username': comment.user.username,
                    'content': comment.content
                })
    # Redirect once after any POST action

    # Optimized fetch
    posts = CommunityPost.objects.select_related('user__profile') \
        .prefetch_related('comments__user__profile') \
        .all().order_by('-created_at')

    return render(request, 'community.html', {'posts': posts})


from django.shortcuts import render, get_object_or_404  # Make sure get_object_or_404 is imported
from .models import SignLesson

@login_required
def videowatcher(request, video_id):
    # Change .all() to get_object_or_404 to look up the specific video by its primary key (pk)
    word_object = get_object_or_404(SignLesson, pk=video_id)

    context = {
        'word': word_object
    }
    return render(request, 'videowatcher.html', context)


# base/views.py
from django.shortcuts import render, redirect
from .forms import IsyaratkuSignUpForm
from django.contrib.auth import login


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dictionary')
    if request.method == 'POST':
        form = IsyaratkuSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/dictionary')
    else:
        form = IsyaratkuSignUpForm()

    return render(request, 'Register.html', {'form': form})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
@login_required
def profile_settings(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST,request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect("dictionary")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'Settings.html', {'form': form})


# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import PageVisit

from django.http import JsonResponse
import json
from .models import PageVisit
from django.views.decorators.csrf import csrf_exempt

def track_time_spent(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON string
            data = json.loads(request.body)

            if not request.session.session_key:
                request.session.create()

            PageVisit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                page_url=data.get('url'),
                duration_seconds=data.get('duration')
            )
            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'invalid method'}, status=405)

import json
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from .models import PageVisit, User


def update_profile_streak(user):
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)

    # Calculate total seconds spent TODAY by this user
    total_seconds_today = PageVisit.objects.filter(
        user=user,
        created_at__date=today
    ).aggregate(total=Sum('duration_seconds'))['total'] or 0.0

    # 20 minutes = 1200 seconds
    if total_seconds_today >= 10:
        # Access the profile directly through the OneToOne related_name 'profile'
        profile = user.profile

        # If they haven't already completed their goal today
        if profile.last_completed_date != today:

            # If they completed it yesterday, increase the streak count!
            if profile.last_completed_date == yesterday:
                profile.streak += 1
            # If they missed yesterday, start a fresh streak at 1
            else:
                profile.streak = 1

            # Update their highest streak record if they beat it
            if profile.streak > profile.max_streak:
                profile.max_streak = profile.streak

            # Lock today in as completed
            profile.last_completed_date = today
            profile.save()
@login_required
def quiz_results(request):
    """
    Renders the beautiful results summary layout page
    """
    context = {
        'module_title': request.GET.get('module', 'Quiz'),
        'score_fraction': request.GET.get('score', '0/0'),
        'accuracy': request.GET.get('accuracy', '0'),
        'points_earned': request.GET.get('points', '0'),
    }
    return render(request, 'quiz_results.html', context)


@login_required
def community_post_feed(request):
    # Handle new post submissions sent directly to this endpoint
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')  # Capture the uploaded file
        if title and content:
            CommunityPost.objects.create(
                user=request.user,
                title=title,
                content=content,
                image=image  # Save the image
            )
            return redirect('community_post_feed')
    posts = CommunityPost.objects.all().order_by('-created_at')

    return render(request, 'community_post.html', {'posts': posts})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import CommunityPost


@login_required
def profile_view(request):
    # Fetch only the items created by the logged-in user, ordered by newest first
    user_posts = CommunityPost.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'posts': user_posts
    }
    return render(request, 'profile.html', context)