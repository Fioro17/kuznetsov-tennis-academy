from django.shortcuts import render

def home(request):
    return render(request, 'pages/home.html')

def academy(request):
    return render(request, 'pages/academy.html')
