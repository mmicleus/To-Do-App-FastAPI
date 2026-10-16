from fastapi import APIRouter,Depends,HTTPException,status,Form,Response
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm


from dependencies import get_current_active_user
from models.loginModels import User,UserSignUp,UserInDB,UserPublic,Token,TokenData
from auth import authenticate_user,create_access_token,get_password_hash
from database.db import fake_users_db,SessionDep
from datetime import timedelta
from sqlmodel import select
from sqlalchemy.exc import IntegrityError



ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()




@router.get("/users/me/")
async def read_users_me(
current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user



# to work on this

@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
    ):
    return [{"item_id": "Foo", "owner": current_user.username}]



@router.post("/token")
async def login_for_access_token(
form_data: Annotated[OAuth2PasswordRequestForm, Depends()],session:SessionDep) -> Token:
    user = authenticate_user(form_data.username, form_data.password,session)
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



@router.post("/sign-up",response_model=UserPublic,status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data:Annotated[UserSignUp,Form()],session:SessionDep
):

    existing_user = session.exec(select(UserInDB).where(UserInDB.username == signup_data.username)).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already registered")


    password = get_password_hash(signup_data.password)

    user:UserInDB = UserInDB.model_validate(signup_data,update={"hashed_password":password})


    session.add(user)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already registered")
        

    
    session.refresh(user)



    return user
    

    