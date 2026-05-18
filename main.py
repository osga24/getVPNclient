import hmac
import hashlib
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from init_db import rebuild_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    rebuild_db()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

BASE = Path(__file__).parent
DB_PATH = BASE / "users.db"
CLIENTS_DIR = BASE / "wg-clients"
SECRET = "ctf-vpn-secret-2025"
COOKIE_NAME = "session"


def get_user(student_id: str) -> dict | None:
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT name, vpn_num, password FROM users WHERE student_id = ?", (student_id,)
    ).fetchone()
    con.close()
    if row:
        return {"name": row[0], "vpn_num": row[1], "password": row[2]}
    return None


def make_token(student_id: str) -> str:
    sig = hmac.new(SECRET.encode(), student_id.encode(), hashlib.sha256).hexdigest()
    return f"{student_id}:{sig}"


def verify_token(token: str) -> str | None:
    try:
        student_id, sig = token.split(":", 1)
        expected = hmac.new(SECRET.encode(), student_id.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            return student_id
    except Exception:
        pass
    return None


def get_current_user(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_token(token)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if get_current_user(request):
        return RedirectResponse("/download")
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
async def login(request: Request, student_id: str = Form(...), password: str = Form(...)):
    student_id = student_id.strip()
    user = get_user(student_id)
    expected = user["password"] if user and user["password"] else student_id[-4:]
    if not user or password != expected:
        return templates.TemplateResponse(
            request, "login.html", {"error": "帳號或密碼錯誤"}, status_code=401
        )
    response = RedirectResponse("/download", status_code=303)
    response.set_cookie(COOKIE_NAME, make_token(student_id), httponly=True, samesite="lax")
    return response


@app.get("/download", response_class=HTMLResponse)
async def download_page(request: Request):
    student_id = get_current_user(request)
    if not student_id:
        return RedirectResponse("/")
    user = get_user(student_id)
    if not user:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        request, "download.html", {"user": user, "student_id": student_id}
    )


@app.get("/download/config")
async def download_config(request: Request):
    student_id = get_current_user(request)
    if not student_id:
        return RedirectResponse("/")
    user = get_user(student_id)
    if not user:
        return RedirectResponse("/")
    config_path = CLIENTS_DIR / f"client-{user['vpn_num']:02d}.conf"
    if not config_path.exists():
        return HTMLResponse("Config 檔案不存在，請聯繫管理員。", status_code=404)
    return FileResponse(
        config_path,
        filename=f"vpn-{student_id}.conf",
        media_type="application/octet-stream",
    )


@app.get("/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie(COOKIE_NAME)
    return response
