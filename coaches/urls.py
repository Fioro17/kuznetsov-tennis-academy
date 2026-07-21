from django.urls import path 
from . import views

urlpatterns = [

    path('', views.coach_list, name='coach_list'),
    path('<int:coach_id>/', views.coach_detail,name='coach_detail')

]