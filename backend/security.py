import hashlib
import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
ALGORITHM = 'HS256'
TOKEN_TTL_MINUTES = 480
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/auth/login')


def hash_password(password: str) -> str:
    return hashlib.sha256(('sd-salt::' + password).encode()).hexdigest()


def create_token(user_id: int, role: str) -> str:
    payload = {
        'sub': str(user_id),
        'role': role,
        'exp': datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail='Недействительный токен')
    user = db.get(User, int(payload.get('sub', 0)))
    if user is None:
        raise HTTPException(status_code=401, detail='Пользователь не найден')
    return user


def require_role(*roles):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail='Недостаточно прав')
        return user
    return checker
