from pwdlib import PasswordHash
from models.loginModels import UserInDB
from datetime import datetime, time, timedelta,timezone
import jwt
from dotenv import dotenv_values


password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

config = dotenv_values(".env")




def get_user(db, username: str):
    if username in db:
        return UserInDB(**db[username])

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
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
    return jwt.encode(to_encode, config["SECRET_KEY"], algorithm=config["ALGORITHM"])