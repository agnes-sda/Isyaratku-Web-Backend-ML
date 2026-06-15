from django.contrib import admin
from django.urls import path, include  # include is needed if using an app urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from base import views  # Import your views directly if you aren't using include()
urlpatterns = [
    path("",views.mainpage,name="mainpage"),
    path("dictionary/", views.home, name='dictionary'),
    path("quizzes/", views.quizzes, name='quizzes'),
    path("practice/", views.practice, name='practice'),
    path("progress/", views.progress, name='progress'),
    path("community/", views.community, name='community'),
    path("video/<int:video_id>/", views.videowatcher, name='video_watcher'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('setting/',views.profile_settings,name='setting'),
    path('api/track-time/', views.track_time_spent, name='track_time'),
    path('quizzes/results/', views.quiz_results, name='quiz_results'),
    path('quizzes/<slug:slug>/', views.take_quiz, name='take_quiz'),
    path('communitypost/', views.community_post_feed, name='community_post_feed'),
    path('profile/', views.profile_view, name='user_profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)