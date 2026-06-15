from django.contrib import admin
from .models import LessonCategory, SignLesson,Profile, PageVisit, QuizModule ,Question,QuizSubmission,CommunityPost,PostComment

admin.site.register(LessonCategory)
admin.site.register(SignLesson)
admin.site.register(Profile)
admin.site.register(PageVisit)
admin.site.register(QuizModule)
admin.site.register(Question)
admin.site.register(QuizSubmission)
admin.site.register(CommunityPost)
admin.site.register(PostComment)