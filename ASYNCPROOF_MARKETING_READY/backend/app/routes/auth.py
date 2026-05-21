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

def get_value(row, key, index):
    if isinstance(row, dict):
        return row[key]
    return row[index]

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

            row = cur.fetchone()
            user_id = get_value(row, "id", 0)

    token = create_token(user_id, data.email)

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": data.name,
            "email": data.email,
            "plan": "free"
        }
    }

@router.post("/login")
def login(data: LoginRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, password_hash, plan, role, created_at
                FROM users
                WHERE email=%s
                """,
                (data.email,)
            )
            user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    password_hash = get_value(user, "password_hash", 3)

    if not verify_password(data.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = get_value(user, "id", 0)
    name = get_value(user, "name", 1)
    email = get_value(user, "email", 2)
    plan = get_value(user, "plan", 4)
    role = get_value(user, "role", 5)

    token = create_token(user_id, email)

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "plan": plan,
            "role": role
        }
    }
