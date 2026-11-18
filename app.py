from rag import retrieve_relevant_chunks
from datetime import datetime, timedelta, timezone
from jose import jwt
from schemas import UserLogin

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from jose import JWTError

from database import get_db
from models import User
from schemas import UserRegister

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import ollama

from database import engine, Base
import models

app = FastAPI(
    title="AI-Powered College Assistant",
    description="College chatbot for students, faculty and administrators",
    version="1.0.0"
)
password_hasher = PasswordHash.recommended()

SECRET_KEY = "QSMYUxRFAZ2ECNWWyQph_w679YgqKioChfXi2YxeCrE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
def create_access_token(user_email: str, user_role: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_email,
        "role": user_role,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "Frontend" / "index.html"


# Request model
class ChatRequest(BaseModel):
    message: str


# Home API
@app.get("/")
def home():
    return {
        "message": "Welcome to AI-Powered College Assistant!",
        "status": "Backend is running successfully"
    }


# Health API
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "College Assistant"
    }


# About API
@app.get("/about")
def about():
    return {
        "project": "AI-Powered College Assistant",
        "users": ["Students", "Faculty", "Admin"]
    }


# Frontend page
@app.get("/chat")
def chat_page():
    return FileResponse(HTML_FILE)

@app.get("/login")
def login_page():
    return FileResponse("Frontend/login.html")

@app.get("/register")
def register_page():
    return FileResponse("Frontend/register.html")

@app.get("/dashboard")
def dashboard_page():
    return FileResponse("Frontend/dashboard.html")


@app.get("/api/dashboard")
def get_dashboard_data(
    current_user: User = Depends(get_current_user)
):
    return {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role
    }

# Chat API
# Chat API
@app.post("/ask")
def ask_question(request: ChatRequest):

    user_message = request.message
    relevant_chunks = retrieve_relevant_chunks(user_message, top_k=3)

    context = "\n\n".join(
        [
            f"Source: {chunk['source']}, Page: {chunk['page']}\n"
            f"Content: {chunk['text']}"
            for chunk in relevant_chunks
        ]
    )

    try:
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI College Assistant. "
                        "Help students, faculty and administrators "
                        "with clear and simple college-related answers. "

                        "Answer the user's question using the following "
                        "college document information:\n\n"

                        f"{context}\n\n"

                        "Important rules:\n"
                        "1. Use the provided context to answer questions.\n"
                        "2. Do not invent college rules, timings or details.\n"
                        "3. If the answer is not available in the context, "
                        "clearly say that the information is not available "
                        "in the provided college documents.\n"
                        "4. Give simple and helpful answers.\n"
                        "5. Mention the source document and page number "
                        "when possible.\n"
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        answer = response["message"]["content"]

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="AI model is unavailable. Please try again."
        )

    return {
        "question": user_message,
        "answer": answer
    }

@app.post("/register", status_code=201)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = password_hasher.hash(
        user_data.password
    )

    # Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password,
        role="student"
    )

    # Save user in database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Registration successful!",
        "user_id": new_user.id,
        "full_name": new_user.full_name,
        "email": new_user.email,
        "role": new_user.role
    }

@app.post("/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not password_hasher.verify(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    access_token = create_access_token(
        user_email=user.email,
        user_role=user.role
    )

    return {
        "message": "Login successful!",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role
    }