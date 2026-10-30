# DailyToDos

A personal task manager with a FastAPI backend and a lightweight HTML, CSS, and JavaScript frontend. Create an account to organise, prioritise, and track your own tasks.



**Demo:** https://dailytodos.fastapicloud.dev

**API docs:** [https://dailytodos.fastapicloud.dev/docs](http://127.0.0.1:8000/docs) after starting the server.

## Features

- Account signup and sign-in using JWT bearer tokens.
- Password hashing with Argon2.
- User-specific tasks with create, list, edit, complete, and delete operations.
- Task priority levels, status filters, and text search.
- Responsive frontend served by the FastAPI application.
- Supabase used for persistent data storage

## Tech stack

- **Backend:** Python 3.13+, FastAPI, Pydantic, SQLModel, Supabase
- **Database:** PostgreSQL
- **Authentication:** OAuth2 password flow, JWT, Argon2
- **Frontend:** HTML, CSS, and vanilla JavaScript
- **Dependency management:** [uv](https://docs.astral.sh/uv/)
- **Tests:** pytest

## Getting started

### Prerequisites

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Install and configure

Clone the repository and enter the project directory:

```shell
git clone https://github.com/mmicleus/To-Do-App-FastAPI.git
cd To-Do-App-FastAPI
```

Install the locked dependencies:

```shell
uv sync
```

Create a local `.env` file from the example. In PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```shell
cp .env.example .env
```

Before using the app beyond local development, replace `SECRET_KEY` in `.env` with a unique random value of at least 32 characters. For example:

```shell
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```



### Run the application

From the project directory:

```shell
uv run fastapi dev main.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the frontend or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API documentation.

## API overview

Protected task routes require an `Authorization: Bearer <access_token>` header. Obtain a token by signing in.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/sign-up` | Create an account |
| `POST` | `/token` | Sign in and receive a bearer token |
| `GET` | `/users/me/` | Get the authenticated user's profile |
| `POST` | `/todos/` | Create a task |
| `GET` | `/todos/` | List the authenticated user's tasks |
| `GET` | `/todos/{id}` | Get one of the user's tasks |
| `PATCH` | `/todos/{id}` | Update a task |
| `DELETE` | `/todos/{id}` | Delete a task |

Use `/docs` for request schemas, parameters, and interactive API requests.

## Project structure

```text
.
├── frontend/       # Static HTML, CSS, and JavaScript
├── database/       # SQLModel engine and database session
├── models/         # User and task data models
├── routers/        # Authentication and task API routes
├── tests/          # Router and unit tests
├── auth.py         # Password hashing and token helpers
├── dependencies.py # Authentication and request validation
└── main.py         # FastAPI app, startup, routers, and frontend
```

## Architecture

The browser uses the same FastAPI origin for the static frontend and JSON API. FastAPI routes authenticate requests, apply user-scoped task access, and use SQLModel sessions to read and write to the database. The database tables are created using SQLModel at application startup.

```text
Browser (HTML/CSS/JavaScript)
       │ same-origin requests
       ▼
FastAPI ── authentication and task routers
       │
       ▼
SQLModel sessions ── SQLite (default) or configured database
```

Passwords are hashed before they are stored. Sign-in issues a short-lived JWT access token, which the frontend sends with protected API requests.

## Running tests

Run the test suite from the project directory:

```shell
uv run pytest
```

- Potential improvements include database migrations, automated CI, and a production deployment with secure token handling.
