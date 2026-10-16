from pydantic import BaseModel
from sqlmodel import SQLModel,Field



class User(SQLModel):
    username: str = Field(index=True,min_length=4, max_length=20)
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



class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


