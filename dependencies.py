
from fastapi import HTTPException,Query,status,Depends
from typing import Annotated
from uuid import UUID
from database.db import todos
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from models.todoModels import ToDoCreate,ToDoItem
from models.loginModels import TokenData, User
import jwt
from jwt.exceptions import InvalidTokenError
from auth import get_user
from database.db import fake_users_db,engine,SessionDep
from sqlmodel import create_engine,Session
from dotenv import dotenv_values


forbidden_tasks = ["drink", "smoke", "gamble","drugs"]

config = dotenv_values(".env")


# ------------------------------------------ database dependencies ------------------------

# sqlite_url = "sqlite:///database.db"



# def get_session():
#     with Session(engine) as session:
#         yield session


# SessionDep = Annotated[Session, Depends(get_session)]



def check_todo_data(todo:ToDoCreate):

    if todo.title.lower() in forbidden_tasks:
        raise HTTPException(status_code=422, detail=f"Task '{todo.title}' is not allowed.")

    
    return todo


class Pagination:
    def __init__(self,limit: Annotated[int,Query(ge=1, le=100, description="Limit the number of to-do items returned")] = 5,skip:Annotated[int,Query(ge=0, description="Skip the first n to-do items")] = 0):
        self.limit = limit
        self.skip = skip





def find_todo_by_id(id: int,session:SessionDep) -> ToDoItem:

    todo = session.get(ToDoItem,id)

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="To-do item not found"
        )
    
    return todo


# def find_todo_by_id(todo_id: UUID) -> ToDoItem:

#     todo = todos.get(todo_id)

#     if not todo:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="To-do item not found"
#         )
    
#     return todo


# ---------------------------------------- login dependencies ----------------------------------

ALGORITHM = "HS256"
SECRET_KEY = "0c7a2c1581781638569e7e947e5f52a8ef1715cb825d8672d7a96fdd065da163"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")








async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],session:SessionDep):
    credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(token_data.username,session)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


ActiveUserDep = Annotated[User, Depends(get_current_active_user)]












