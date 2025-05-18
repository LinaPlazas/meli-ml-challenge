from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import AuthService
from app.config.db import MongoDB
from fastapi import Form
from pydantic import BaseModel,SecretStr

router = APIRouter()
auth_service = AuthService()
mongo = MongoDB()

@router.post("/token")
async def login_for_access_token(
    username: str = Form(...),
    password: SecretStr = Form(..., min_length=1, max_length=100, description="Your password", type="password")):
    user = await mongo.get_user_from_db(username)
    if not user or not auth_service.verify_password(password.get_secret_value(), user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}
