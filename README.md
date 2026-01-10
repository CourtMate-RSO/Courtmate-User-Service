CourtMate — User Service

FastAPI microservice responsible for user authentication, profile management and identity-related APIs for the CourtMate platform.

## Table of Contents


- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Project Structure](#project-structure)


## Key Features

- User registration and login (email/password)
- Social login (Google OAuth) integration
- Email verification flow
- User profile retrieval and updates
- JWT token issuance and validation
- Integration with Supabase for persistence and auth where applicable

## Technology Stack

- Framework: FastAPI
- Data/Auth: Supabase (Postgres + Auth)
- HTTP server: Uvicorn
- Dependency management: requirements.txt
- Containerization: Docker / docker-compose (optional)

## API Endpoints

Primary endpoints are prefixed with `/auth` or `/user` (see routes in `app/main.py` / `app/auth_handler.py`):

- `POST /auth/signup` — Register new user (email, password)
- `POST /auth/login` — Login and return JWT
- `POST /auth/google` — Google OAuth callback (token exchange)
- `GET /auth/me` — Get current user from token
- `GET /user/{user_id}` — Retrieve user profile
- `PUT /user/{user_id}` — Update user profile
- `GET /health` — Health check

## Project Structure

```
Courtmate-User-Service/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry
│   ├── auth_handler.py    # Authentication routes and logic
│   ├── models.py          # Pydantic models / DTOs
│   ├── supabase_client.py # Supabase wrapper
│   └── ...
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```



