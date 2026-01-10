from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.models import (
    SignupRequest, LoginRequest, GoogleAuthRequest, RefreshTokenRequest, UserUpdateRequest
)
from app.auth_handler import verify_jwt_token
from app.supabase_client import (
    anon_supabase_client, user_supabase_client, admin_supabase_client
)
import os
import logging
import sys
from dotenv import load_dotenv
import httpx
from fastapi.middleware.cors import CORSMiddleware

# Structured JSON logging setup
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("user-service")
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    rename_fields={"levelname": "level", "asctime": "timestamp"}
)
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Load environment variables from .env file
load_dotenv()

AUTH_PREFIX = "/auth"
USER_PREFIX = "/user"
ENV = os.getenv("ENV", "dev")

# FastAPI app - Enable docs for documentation generation
app = FastAPI(
    title="User & Authentication API",
    description="API for user management and authentication with Supabase.",
    version="1.0.0",
    openapi_url=f"{AUTH_PREFIX}/openapi.json",
    docs_url=f"{AUTH_PREFIX}/docs",
    redoc_url=f"{AUTH_PREFIX}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Security and Supabase configurations
security = HTTPBearer()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "Missing SUPABASE_URL, SUPABASE_ANON_KEY, or SUPABASE_SERVICE_ROLE_KEY in environment variables")

# Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}


@app.get(f"{AUTH_PREFIX}/")
async def root():
    return {"message": "Hello World"}


@app.post(f"{AUTH_PREFIX}/signup")
async def signup(request: SignupRequest):
    """Sign up with email and password"""
    try:
        supabase = anon_supabase_client()
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Signup failed")
        
        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "access_token": response.session.access_token if response.session else None,
            "refresh_token": response.session.refresh_token if response.session else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(f"{AUTH_PREFIX}/login")
async def login(request: LoginRequest):
    """Login with email and password"""
    try:
        supabase = anon_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(f"{AUTH_PREFIX}/google")
async def google_auth(request: GoogleAuthRequest):
    """Authenticate with Google OAuth"""
    try:
        supabase = anon_supabase_client()
        
        # Sign in with Google OAuth using Supabase
        response = supabase.auth.sign_in_with_id_token({
            "provider": "google",
            "token": request.id_token,
        })
        
        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Google authentication failed")
        
        # Check if user profile exists in users_data table
        admin_supabase = admin_supabase_client()
        try:
            user_data = admin_supabase.table("users_data").select("*").eq("id", response.user.id).execute()
            
            if not user_data.data or len(user_data.data) == 0:
                # Create user profile for new Google sign-in
                admin_supabase.table("users_data").insert({
                    "id": response.user.id,
                    "email": request.email,
                    "full_name": request.name or request.email.split("@")[0],
                }).execute()
        except Exception as profile_error:
            # If table doesn't exist or other errors, just log it
            print(f"User profile creation skipped: {profile_error}")
        
        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(f"{AUTH_PREFIX}/refresh_token", dependencies=[Depends(verify_jwt_token)])
async def refresh_token(request: RefreshTokenRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
        headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
        payload = {"refresh_token": request.refresh_token}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return {
                "accessToken": data.get("access_token"),
                "refreshToken": data.get("refresh_token"),
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("error", "Error refreshing access token"),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(
            e) or "Unexpected error refreshing access token.")
    
@app.get(f"{AUTH_PREFIX}/me", dependencies=[Depends(verify_jwt_token)])
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        supabase = user_supabase_client(token)
        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# Get user by ID using GraphQL
@app.get(f"{USER_PREFIX}/{{user_id}}", dependencies=[Depends(verify_jwt_token)])
async def get_user_by_id(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        
        # Use GraphQL instead of Supabase client
        from app.graphql_client import get_user_by_id_graphql
        user = get_user_by_id_graphql(user_id, token)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
# Update users data row
@app.put(f"{USER_PREFIX}/{{user_id}}", dependencies=[Depends(verify_jwt_token)])
async def update_user(user_id: str, update_data: UserUpdateRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        supabase = user_supabase_client(token)
        
        # Update user data - RLS policies will handle authorization
        user = supabase.table("users_data").update(update_data.dict(exclude_unset=True)).eq("id", user_id).execute()
        return user.data
    except Exception as e:
        print(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))