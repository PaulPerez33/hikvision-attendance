# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta
from app import models
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_db,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Schemas
class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: str  # "admin" o "teacher"

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

@router.post("/register", response_model=UserOut)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario (admin o teacher)"""
    # Verificar que el username no exista
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    # Validar rol
    if user_data.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol debe ser 'admin' o 'teacher'"
        )
    
    # Crear usuario
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login con username y password, retorna JWT token"""
    # Buscar usuario
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
async def get_me(current_user: models.User = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    """Listar todos los usuarios"""
    users = db.query(models.User).all()
    return users
