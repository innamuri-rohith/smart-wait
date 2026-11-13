# SmartWait

SmartWait is a FastAPI-based queue and service-management platform for academic and administrative workflows. It supports student, staff, and admin roles, service counters, token-based queues, visit planning, and role-specific portals.

## Features

- Student registration and secure login
- Role-based access for students, staff, and admins
- Queue token management for service counters
- Service and counter configuration
- Visit planning with service dependencies
- Portal endpoints tailored to each role
- SQLite by default for local development
- FastAPI automatic OpenAPI docs

## Project structure

```text
smartwait/
├── .env                     # local environment configuration
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── schemas/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── pytest.ini
├── docs/
├── pyrightconfig.json
├── smartwait.db
└── README.md
```

## Tech stack

- Python 3.13
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite (development)
- JWT authentication
- Pytest

## Getting started

1. Open a terminal in the project root.
2. Create and activate a virtual environment:

```bash
cd smartwait
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

4. Configure environment variables.

The project uses a `.env` file in the `smartwait/` directory. A sample configuration is already present in the project root and includes the database URL and JWT settings.

5. Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API overview

Primary API routers:

- `/api/auth` - registration, login, and current user info
- `/api/portal` - role-specific portal data
- `/api/admin` - administrative functions
- `/api/health` - health check endpoint

## Development notes

- Database initialization happens automatically when the FastAPI app starts.
- Default local database: `smartwait.db`
- JWT secret and CORS settings are loaded from the environment configuration.

## Testing

Run the test suite with:

```bash
cd backend
pytest
```

## License

This project is intended for internal or educational use unless otherwise specified by the repository owner.
