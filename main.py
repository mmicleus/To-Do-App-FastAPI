from fastapi import FastAPI,HTTPException,Path,Query,Body,Form,UploadFile,File,status,Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field, AfterValidator
from uuid import UUID
import uuid
from typing import Annotated, Optional
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware



from routers import login,todo





app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this in production
    allow_methods=["*"],
    allow_headers=["*"],
    
)



app.include_router(todo.router)

# login




def has_alphanumeric(password: str):
    for ch in password:
        if ch.isalnum():
            return True
    return False


# def has_special_character(password: str):

#     for ch in password:
#         if ch in ["@", "#", "$", "%", "^", "&", "*"]:
#             return True   
#     return False

def has_special_character(password: str):
    special_characters = set("@#$%^&*")
    return any(ch in special_characters for ch in password)





def validate_password(password: str):
    if len(password) < 8 or len(password) > 30:
        raise HTTPException(status_code=422, detail="Password must be between 8 and 30 characters long")
    elif not has_alphanumeric(password):
        raise HTTPException(status_code=422, detail="Password must contain at least one alphanumeric character")
    elif not has_special_character(password):
        raise HTTPException(status_code=422, detail="Password must contain at least one special character (@, #, $, %, ^, &, *)")
    return password


# class FormData(BaseModel):
#     username: Annotated[str,Field(description="Username for login", min_length=4, max_length=20)]
#     password: Annotated[str, AfterValidator(validate_password), Field(description="Password for login", min_length=8, max_length=30)]

   
class FormData(BaseModel):
    username: str
    password: str


# @app.post("/login",tags=["Authentication"],summary="Login endpoint", description="Endpoint for user login with username and password validation")
# async def Login(file: Annotated[UploadFile, File()],username: Annotated[str, Form(min_length=4, max_length=20)], password: Annotated[str,AfterValidator(validate_password), Form(min_length=8, max_length=30)]):

#     return {"message": "Login successful"}


    


