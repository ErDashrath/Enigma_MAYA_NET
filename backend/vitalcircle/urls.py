"""
URL configuration for vitalcircle project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from ninja import NinjaAPI
from ninja.errors import HttpError

from core.auth import JWTAuth, create_jwt_token
from core.schemas import LoginSchema, RegisterSchema, TokenSchema, MessageSchema, ErrorSchema, UserSchema

# Create the main API instance
api = NinjaAPI(
    title="VitalCircle API", 
    version="1.0.0",
    description="Predictive Chronic Care Ecosystem API"
)

# Initialize JWT Auth
jwt_auth = JWTAuth()

@api.get("/health")
def health_check(request):
    """Health check endpoint"""
    return {"status": "healthy", "message": "VitalCircle API is running"}


@api.post("/auth/register", response={201: TokenSchema, 400: ErrorSchema})
def register(request, payload: RegisterSchema):
    """Register a new user"""
    try:
        # Check if user already exists
        if User.objects.filter(username=payload.username).exists():
            return 400, {"error": "Username already exists"}
        
        if User.objects.filter(email=payload.email).exists():
            return 400, {"error": "Email already exists"}
        
        # Create new user
        user = User.objects.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name or "",
            last_name=payload.last_name or ""
        )
        
        # Create JWT token
        token = create_jwt_token(user)
        
        user_data = UserSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            date_joined=user.date_joined.isoformat()
        )
        
        return 201, {
            "access_token": token,
            "token_type": "bearer",
            "user": user_data
        }
        
    except Exception as e:
        return 400, {"error": "Registration failed", "detail": str(e)}


@api.post("/auth/login", response={200: TokenSchema, 401: ErrorSchema})
def login(request, payload: LoginSchema):
    """Login user and return JWT token"""
    user = authenticate(username=payload.username, password=payload.password)
    
    if not user:
        return 401, {"error": "Invalid credentials"}
    
    if not user.is_active:
        return 401, {"error": "Account is disabled"}
    
    # Create JWT token
    token = create_jwt_token(user)
    
    user_data = UserSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        date_joined=user.date_joined.isoformat()
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }


@api.get("/auth/me", auth=jwt_auth, response=UserSchema)
def get_current_user(request):
    """Get current authenticated user"""
    user = request.auth
    return UserSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        date_joined=user.date_joined.isoformat()
    )


@api.get("/protected", auth=jwt_auth)
def protected_endpoint(request):
    """Example protected endpoint"""
    return {"message": f"Hello {request.auth.username}! This is a protected endpoint."}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # All API endpoints will be under /api/
]
