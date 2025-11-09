from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.models import (
    SignupRequest,LoginRequest, RefreshTokenRequest, UserUpdateRequest
)
from app.auth_handler import verify_jwt_token
from app.supabase_client import (
    anon_supabase_client, user_supabase_client
)
import os
from dotenv import load_dotenv
import httpx
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

AUTH_PREFIX = "/auth"
USER_PREFIX = "/user"
ENV = os.getenv("ENV", "dev")

# FastAPI app
if ENV == "prod":
    app = FastAPI(
        title="Authentication API",
        description="API for managing user authentication.",
        version="1.0.0",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
else:
    app = FastAPI(
        title="Authentication API",
        description="API for managing user authentication.",
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

# Security and Supabase configurations
security = HTTPBearer()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "Missing SUPABASE_URL, SUPABASE_ANON_KEY, or SUPABASE_SERVICE_ROLE_KEY in environment variables")

# Endpoints
@app.get(f"{AUTH_PREFIX}/")
async def root():
    return {"message": "Hello World"}


@app.post(f"{AUTH_PREFIX}/signup")
async def signup(request: SignupRequest):
    try:
        supabase = anon_supabase_client()
        user = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(f"{AUTH_PREFIX}/login")
async def login(request: LoginRequest):
    try:
        supabase = anon_supabase_client()
        user = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        return user
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
    

# Get user by ID
@app.get(f"{USER_PREFIX}/{{user_id}}", dependencies=[Depends(verify_jwt_token)])
async def get_user_by_id(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        supabase = user_supabase_client(token)
        supabase.auth.set_session(access_token=token, refresh_token="")
        user = supabase.table("users_data").select("*").eq("id", user_id).single().execute()
        return user.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Update users data row
@app.put(f"{USER_PREFIX}/{{user_id}}", dependencies=[Depends(verify_jwt_token)])
async def update_user(user_id: str, update_data: UserUpdateRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        supabase = user_supabase_client(token)
        supabase.auth.set_session(access_token=token, refresh_token="")
        user = supabase.table("users_data").update(update_data.dict(exclude_unset=True)).eq("id", user_id).execute()
        return user.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))