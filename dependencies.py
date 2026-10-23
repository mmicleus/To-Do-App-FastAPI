
from fastapi import HTTPException,Query,status,Depends
from typing import Annotated
from uuid import UUID
from database.db import todos
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from models.todoModels import ToDoCreate,ToDoItem
from models.loginModels import TokenData, User,UserInDB
import jwt
from jwt.exceptions import InvalidTokenError
from auth import get_user
from database.db import fake_users_db,engine,SessionDep
from sqlmodel import create_engine,Session,select
from config import settings



forbidden_tasks = ["drink", "smoke", "gamble","drugs"]




# ------------------------------------------ database dependencies ------------------------

# sqlite_url = "sqlite:///database.db"



# def get_session():
#     with Session(engine) as session:
#         yield session


# SessionDep = Annotated[Session, Depends(get_session)]


#validates a todo item 
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









# ---------------------------------------- login dependencies ----------------------------------








oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")








def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],session:SessionDep):
    credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm])
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


def get_current_active_user(
current_user: Annotated[UserInDB, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


#returns the current active user as a UserInDB instance if a valid AWT token exists
ActiveUserDep = Annotated[UserInDB, Depends(get_current_active_user)]

FindToDoByIdDep = Annotated[ToDoItem,Depends(find_todo_by_id)]


#gets the current active user using the "ActiveUserDep" dependency injection
# fetches the to do item with the id set in the path parameter
#checks if the todo item belongs to the current active user
#return the todo
def get_userTodo_by_id(user:ActiveUserDep,todo:FindToDoByIdDep) -> ToDoItem:

    
    if todo.user_id != user.id:
            
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Forbidden from accessing this item!")

    return todo

# gets the current active user using the "ActiveUserDep" dependency injection 
# fetches all the current active user's to do items within the limits set by pagination
def getUserToDosWithPagination(user:ActiveUserDep,pagination: Annotated[Pagination,Depends()], session:SessionDep) -> list[ToDoItem]:

    user_todos = session.exec(select(ToDoItem).where(ToDoItem.user_id == user.id).offset(pagination.skip).limit(pagination.limit)).all()
    return user_todos


#gets the current active user using the "ActiveUserDep" dependency injection
# fetches the to do item with the id set in the path parameter
#checks if the todo item belongs to the current active user
#return the todo
FindUserToDoByIdDep = Annotated[ToDoItem,Depends(get_userTodo_by_id)]

#validates the new todo item created by the user
ValidateToDoDep = Annotated[ToDoCreate,Depends(check_todo_data)]


# gets the current active user using the "ActiveUserDep" dependency injection and fetches all the current active user's to do items within the limits set by pagination
GetUserToDosWithPaginationDep = Annotated[list[ToDoItem],Depends(getUserToDosWithPagination)]

    














