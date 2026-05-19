from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.db.database import get_conn, row_to_dict
from app.services.security import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(data: RegisterRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
            existing = cur.fetchone()
            if existing:
                raise HTTPException(status_code=409, detail="Email already registered")
            cur.execute(
                """
                INSERT INTO users(name,email,password_hash)
                VALUES(%s,%s,%s)
                RETURNING id
                """,
                (data.name, data.email, hash_password(data.password))
            )
            user_id = cur.fetchone()["id"]
    token = create_token(user_id, data.email)
    return {"token": token, "user": {"id": user_id, "name": data.name, "email": data.email, "plan": "free"}}

@router.post("/login")
def login(data: LoginRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (data.email,))
            user = cur.fetchone()
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"], user["email"])
    safe_user = row_to_dict(user)
    safe_user.pop("password_hash", None)
    return {"token": token, "user": safe_user}
