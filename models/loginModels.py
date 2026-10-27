from pydantic import BaseModel
from sqlmodel import SQLModel,Field, Relationship,Column,DateTime
from enum import Enum
from datetime import datetime, timezone
# from models.todoModels import ToDoItem



class Activity(Enum):
    SignUp = 1
    SignIn = 2


class User(SQLModel):
    username: str = Field(index=True,unique=True,min_length=4, max_length=20)
    email: str | None = None
    full_name: str | None = Field(index=True, min_length=4, max_length=20)
    disabled: bool | None = None


class UserSignUp(User):
    password:str = Field(min_length=6,max_length=30)


    
class UserPublic(User):
     id: int



class UserInDB(User,table=True):
    id: int | None = Field(default=None,primary_key=True)
    hashed_password: str # never expose this in responses
    todos:list["ToDoItem"] = Relationship(back_populates="user",cascade_delete=True)



class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# used to log user sign ups and sign ins

class ActivityLog(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True, description="unique activity ID")
    user_id : int = Field(foreign_key="userindb.id")
    activity : Activity
    occured_at : datetime = Field(
        #will set the value of occured_at on object creation by calling utc_now()
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )








