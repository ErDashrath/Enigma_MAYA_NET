"""
Django views for VitalCircle frontend templates and API
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .auth import create_jwt_token, verify_jwt_token
import json


def home_view(request):
    """Home page view"""
    # Mock statistics - replace with real data later
    stats = {
        'total_patients': 1200,
        'total_vitals': 25600,
        'risk_prevention_rate': 89
    }
    return render(request, 'home.html', {'stats': stats})


@login_required
def dashboard_view(request):
    """Main dashboard for authenticated users"""
    # Mock user health data - replace with real data from database
    context = {
        'user': request.user,
        'stability_score': 85,
        'risk_level': 'low',
        'recent_vitals': {
            'blood_pressure': '120/80',
            'heart_rate': 72,
            'stress_level': 3,
            'sodium_intake': 1800
        },
        'nudges': [
            "Great job maintaining your blood pressure!",
            "Consider reducing sodium intake by 200mg",
            "Your stress levels are optimal - keep it up!"
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required
def vitals_view(request):
    """Vitals input and history page"""
    if request.method == 'POST':
        # Handle vitals form submission
        messages.success(request, 'Vitals recorded successfully!')
        return redirect('vitals')
    
    return render(request, 'vitals.html')


@login_required
def reports_view(request):
    """Health reports and analytics page"""
    return render(request, 'reports.html')


def login_view(request):
    """JWT-based login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Create JWT token
            token = create_jwt_token(user)
            
            # For template-based views, we still use Django sessions
            login(request, user)
            
            # Store token in session for API usage
            request.session['jwt_token'] = token
            
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


@csrf_exempt
def api_login(request):
    """JWT API login endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(username=username, password=password)
            if user is not None:
                token = create_jwt_token(user)
                return JsonResponse({
                    'success': True,
                    'token': token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_register(request):
    """JWT API registration endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            
            # Basic validation
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Username already exists'
                }, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Email already registered'
                }, status=400)
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create JWT token for new user
            token = create_jwt_token(user)
            
            return JsonResponse({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def register_view(request):
    """Template-based registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user_type = request.POST.get('user_type', 'patient')
        
        # Basic validation
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user profile with user_type
        from .models import UserProfile
        UserProfile.objects.create(
            user=user,
            user_type=user_type
        )
        
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')
    
    return render(request, 'auth/register.html')


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile page"""
    return render(request, 'auth/profile.html')


# API endpoint for AJAX requests
@csrf_exempt
@login_required
def api_stability_score(request):
    """API endpoint to get user's current stability score"""
    # Mock data - replace with real calculation
    score_data = {
        'score': 85,
        'risk_level': 'low',
        'last_updated': '2025-09-20T10:30:00Z',
        'factors': {
            'blood_pressure': 'normal',
            'heart_rate': 'optimal',
            'stress': 'low',
            'sodium': 'slightly_high'
        }
    }
    return JsonResponse(score_data)


def webllm_test_view(request):
    """WebLLM test interface view"""
    return render(request, 'webllm_test.html')
