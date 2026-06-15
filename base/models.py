

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
class LessonCategory(models.Model):
    """Stores categories like Greetings, Daily Life, Emotions, etc."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# models.py
from django.db import models
from django.contrib.auth.models import User

class PageVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40)
    page_url = models.CharField(max_length=255)
    duration_seconds = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.page_url} - {self.duration_seconds}s"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    score = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)  # Keeps track of current streak
    max_streak = models.IntegerField(default=0)  # 🆕 Tracks their personal high score
    last_completed_date = models.DateField(null=True, blank=True)  # 🆕 Tracks when they hit 20 mins
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png', blank=True)

    def __string__(self):
        return f"{self.user.username}'s Profile"

# Automatically create a Profile instance whenever a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
class SignLesson(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=100, unique=True)
    thumbnail = models.ImageField(upload_to="lesson_thumbnails/")
    video_file = models.FileField(upload_to="lesson_videos/")
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner')

    # NEW FIELDS FOR FILTERING:

    # 1. To filter by A-Z alphabet signs.
    # Can be null/blank if a video is a full word (like "Hello") instead of just a single letter sign.
    letter = models.CharField(max_length=1, blank=True, null=True, choices=[(chr(i), chr(i)) for i in range(65, 91)])

    # 2. To filter by Categories (Greetings, Emotions, etc.).
    # A lesson can belong to multiple categories (e.g., "Hello" is both 'Common Words' and 'Greetings').
    categories = models.ManyToManyField(LessonCategory, related_name="lessons", blank=True)

    # User Interactions
    bookmarked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="bookmarked_lessons", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


from django.db import models
from django.contrib.auth.models import User


class QuizModule(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    thumbnail = models.ImageField(upload_to='quiz_thumbnails/', blank=True, null=True)

    # --- ADD THIS LINE TO CONNECT TO YOUR CATEGORIES ---
    category = models.ForeignKey(
        LessonCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quizzes'
    )

    def __str__(self):
        return self.title


class Question(models.Model):
    module = models.ForeignKey(QuizModule, on_delete=models.CASCADE, related_name='questions')
    sign_video = models.FileField(upload_to='quiz_videos/', help_text="Upload a video/GIF file showing the ASL sign")
    correct_answer = models.CharField(max_length=100)
    option_b = models.CharField(max_length=100)
    option_c = models.CharField(max_length=100)
    option_d = models.CharField(max_length=100)

    def __str__(self):
        return f"Question for {self.module.title}"


class QuizSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(QuizModule, on_delete=models.CASCADE)
    score_fraction = models.CharField(max_length=20)  # e.g., "18/20"
    accuracy_percentage = models.IntegerField()  # e.g., 90
    created_at = models.DateTimeField(auto_now_add=True)




class CommunityPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    # Add this line
    image = models.ImageField(upload_to='community_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PostComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"