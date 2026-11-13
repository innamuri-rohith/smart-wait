"""SmartWait FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api import admin, auth, portal, queue
from app.core.config import settings
from app.db.database import init_db

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SmartWait API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(portal.router, prefix="/api/portal", tags=["portal"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])


@app.get("/", response_class=HTMLResponse)
async def home():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>SmartWait API Running</h1><p>Visit <a href='/docs'>/docs</a></p>")


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    login_file = STATIC_DIR / "login.html"
    if login_file.exists():
        return HTMLResponse(content=login_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Login page</h1><p><a href='/'>Back</a></p>")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    dashboard_file = STATIC_DIR / "dashboard.html"
    if dashboard_file.exists():
        return HTMLResponse(content=dashboard_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard page</h1><p><a href='/'>Back</a></p>")


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name}
