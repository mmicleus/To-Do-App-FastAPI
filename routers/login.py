from fastapi import APIRouter,Depends,HTTPException,status,Form,Response,BackgroundTasks
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm


from dependencies import get_current_active_user
from models.loginModels import User,UserSignUp,UserInDB,UserPublic,Token,TokenData,ActivityLog,Activity
from auth import authenticate_user,create_access_token,get_password_hash
from database.db import fake_users_db,SessionDep
from datetime import timedelta
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from auth import log_activity



ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()




@router.get("/users/me/",response_model=UserPublic)
def read_users_me(
current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


# def log_activity(user:UserInDB,act:Activity,session:SessionDep):

#     activityLog:ActivityLog = ActivityLog(user_id=user.id,activity=act)


#     session.add(activityLog)
#     session.commit()
    



@router.post("/token")
def login_for_access_token(
form_data: Annotated[OAuth2PasswordRequestForm, Depends()],background_tasks:BackgroundTasks,session:SessionDep) -> Token:
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


    #logging user sign in with a timestamp
    background_tasks.add_task(log_activity,user,Activity.SignIn,session)

    return Token(access_token=access_token, token_type="bearer")









@router.post("/sign-up",response_model=UserPublic,status_code=status.HTTP_201_CREATED)
def signup(
    signup_data:UserSignUp,session:SessionDep,
    background_tasks:BackgroundTasks
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

    #logging user sign up with a timestamp

    background_tasks.add_task(log_activity,user,Activity.SignUp,session)

    return user



    

    