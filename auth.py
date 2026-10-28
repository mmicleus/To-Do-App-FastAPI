from pwdlib import PasswordHash
from models.loginModels import UserInDB
from datetime import datetime, time, timedelta,timezone
import jwt
from dotenv import dotenv_values
from database.db import SessionDep
from sqlmodel import select
from fastapi import HTTPException,status
from typing import Optional
from config import settings
from models.loginModels import User,UserSignUp,UserInDB,UserPublic,Token,TokenData,ActivityLog,Activity

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")






def get_user(username: str,session:SessionDep) -> Optional[UserInDB]:

    user = session.exec(select(UserInDB).where(UserInDB.username == username)).first()

   
    return user



def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def authenticate_user(username: str, password: str,session):
    user = get_user(username,session)
    if not user:
        verify_password(password, DUMMY_HASH) # similar timing: blocks username enumeration
        return False
    
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)



def log_activity(user:UserInDB,act:Activity,session:SessionDep):

    activityLog:ActivityLog = ActivityLog(user_id=user.id,activity=act)

    session.add(activityLog)
    session.commit()
    