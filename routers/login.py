from fastapi import APIRouter,Depends,HTTPException,status
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm


from dependencies import get_current_active_user
from models.loginModels import User,Token,TokenData
from auth import authenticate_user,create_access_token
from database.db import fake_users_db
from datetime import timedelta



ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()




@router.get("/users/me/")
async def read_users_me(
current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user



@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
    ):
    return [{"item_id": "Foo", "owner": current_user.username}]



@router.post("/token")
async def login_for_access_token(
form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
    )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=access_token, token_type="bearer")