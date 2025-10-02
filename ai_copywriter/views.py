from django.shortcuts import render, redirect

def home(request):
    # If user is logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('generator:dashboard')
    return render(request, 'home.html')
