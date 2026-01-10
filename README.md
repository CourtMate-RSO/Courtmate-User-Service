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

Primary endpoints are exposed under the `/api/users` prefix (see routes in `app/main.py` / `app/auth_handler.py`):

- `GET /api/users/health` — Health check
- `POST /api/users/auth/signup` — Register new user (email, password)
- `POST /api/users/auth/login` — Login and return JWT
- `POST /api/users/auth/google` — Google OAuth login
- `POST /api/users/auth/refresh` — Refresh access token
- `GET /api/users/user/me` — Get profile of authenticated user (requires bearer token)
- `PUT /api/users/user/update` — Update authenticated user's profile (requires bearer token)

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



