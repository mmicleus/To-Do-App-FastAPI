from pydantic import BaseModel,EmailStr,field_validator
from sqlmodel import SQLModel,Field, Relationship,Column,DateTime
from enum import Enum
from datetime import datetime, timezone
# from models.todoModels import ToDoItem
import string



class Activity(Enum):
    SignUp = 1
    SignIn = 2


class User(SQLModel):
    username: str = Field(index=True,unique=True,min_length=4, max_length=20)
    email: EmailStr = Field(index=True,unique=True)
    disabled: bool | None = None

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not (4 <= len(v) <= 20):
            raise ValueError("Username must be between 4 and 20 characters long")
        return v


    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()




class UserSignUp(User):
    password:str = Field(min_length=6,max_length=30)


    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if not (8 <= len(v) <= 30):
            raise ValueError("Password must be between 8 and 30 characters long")
        if not any(c in string.punctuation for c in v):
            raise ValueError("Password must contain at least one special character")
        if not any(c in string.ascii_letters for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


    
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








