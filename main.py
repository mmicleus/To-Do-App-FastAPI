from fastapi import FastAPI,HTTPException,Path,Query,Body,Form,UploadFile,File,status,Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field, AfterValidator
from uuid import UUID
import uuid
from typing import Annotated, Optional
from enum import Enum



app = FastAPI()

class Urgency(str,Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"



class ToDoBase(BaseModel):
    title: str = Field(description="Title of the to-do item", min_length=1, max_length=20)
    description: Optional[str] = Field(default=None, description="Description of the to-do item", max_length=50)
    completed: bool = False
    urgency: Urgency = Urgency.LOW


class ToDoCreate(ToDoBase):
    pass

class ToDoUpdate(ToDoBase):
    title: str = Field(description="Title of the to-do item", min_length=1, max_length=20)
    description: Optional[str] = Field(..., description="Description of the to-do item", max_length=50)
    completed: bool
    urgency: Urgency





class ToDoItem(ToDoBase):
    id: UUID = Field(description="Unique identifier for the to-do item")


todos = {}
forbidden_tasks = ["drink", "smoke", "gamble","drugs"]

def find_todo_by_id(todo_id: UUID):
    return todos.get(todo_id)


def check_todo_data(todo:ToDoCreate):

    if todo.title.lower() in forbidden_tasks:
        raise HTTPException(status_code=422, detail=f"Task '{todo.title}' is not allowed.")

    
    return todo
    

@app.post("/todos/",tags=["CRUD"])
async def create_todo(todo: Annotated[ToDoCreate,AfterValidator(check_todo_data)],response:Response) -> ToDoItem:

    #generate a random id for the new to-do item
    new_id = uuid.uuid4()

    todoItem = ToDoItem(id=new_id, **todo.model_dump())

    todos[new_id] = todoItem

    
    response.headers["Location"] = f"/todos/{new_id}"

    return todoItem


@app.get("/todos/",response_model=list[ToDoItem],tags=["CRUD"])

async def get_all_todos(limit:Annotated[int,Query(ge=1, le=100, description="Limit the number of to-do items returned")] = 5, skip:Annotated[int,Query(ge=0, description="Skip the first n to-do items")] = 0):
    return list(todos.values())[skip:skip+limit]  



@app.get("/todos/{id}",response_model=ToDoItem,tags=["CRUD"])
async def get_todo(id: UUID):

    todo = find_todo_by_id(id)

    if not todo:
        raise HTTPException(status_code=404, detail="To-do item not found")

    if todo.urgency == Urgency.HIGH:
        print("This is a high urgency task!")

    
    return todo




 


@app.put("/todos/{id}", response_model=ToDoItem,tags=["CRUD"])
async def update_todo(id: UUID, updated_todo: ToDoUpdate):

    todo = find_todo_by_id(id)

    if not todo:
        raise HTTPException(status_code=404, detail="To-do item not found")




    aux = todo.model_copy(update=updated_todo.model_dump())

    todos[todo.id] = aux


    return todos[todo.id] 





@app.delete("/todos/{id}",tags=["CRUD"],status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(id: UUID) -> Response:

    todo = find_todo_by_id(id)

    if not todo:
        raise HTTPException(status_code=404, detail="To-do item not found")

    del todos[todo.id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@app.post("/login",tags=["Authentication"],summary="Login endpoint", description="Endpoint for user login with username and password validation")
async def Login(file: Annotated[UploadFile, File()],username: Annotated[str, Form(min_length=4, max_length=20)], password: Annotated[str,AfterValidator(validate_password), Form(min_length=8, max_length=30)]):

    return {"message": "Login successful"}


    


