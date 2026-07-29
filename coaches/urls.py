from django.urls import path 
from . import views

app_name = 'coaches'

urlpatterns = [

    path('', views.coach_list, name='coach_list'),
    path('my-lessons/',views.my_lessons, name='my_lessons'),
    path('<int:coach_id>/', views.coach_detail,name='coach_detail'),
    path('<int:coach_id>/book/', views.book_lesson, name='book_lesson'),
    path('lessons/<int:lesson_id>/cancel/', views.cancel_lesson, name='cancel_lesson'),
    path('schedule/', views.coach_schedule, name='coach_schedule'),
]