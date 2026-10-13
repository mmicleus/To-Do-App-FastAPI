from fastapi import APIRouter,Query,HTTPException,Response,status
from typing import Annotated, Optional
import uuid
from uuid import UUID
from pydantic import AfterValidator


from models.todoModels import Urgency, ToDoBase,ToDoCreate,ToDoUpdate,ToDoItem


router = APIRouter(prefix="/todos")


todos = {}
forbidden_tasks = ["drink", "smoke", "gamble","drugs"]

def find_todo_by_id(todo_id: UUID):
    return todos.get(todo_id)


def check_todo_data(todo:ToDoCreate):

    if todo.title.lower() in forbidden_tasks:
        raise HTTPException(status_code=422, detail=f"Task '{todo.title}' is not allowed.")

    
    return todo
    

@router.post("/",tags=["CRUD"])
async def create_todo(todo: Annotated[ToDoCreate,AfterValidator(check_todo_data)],response:Response) -> ToDoItem:

    #generate a random id for the new to-do item
    new_id = uuid.uuid4()

    todoItem = ToDoItem(id=new_id, **todo.model_dump())

    todos[new_id] = todoItem

    
    response.headers["Location"] = f"/todos/{new_id}"

    return todoItem


@router.get("/todos/",response_model=list[ToDoItem],tags=["CRUD"])

async def get_all_todos(limit:Annotated[int,Query(ge=1, le=100, description="Limit the number of to-do items returned")] = 5, skip:Annotated[int,Query(ge=0, description="Skip the first n to-do items")] = 0):
    return list(todos.values())[skip:skip+limit]  



@router.get("/todos/{id}",response_model=ToDoItem,tags=["CRUD"])
async def get_todo(id: UUID):

    todo = find_todo_by_id(id)

    if not todo:
        raise HTTPException(status_code=404, detail="To-do item not found")

    if todo.urgency == Urgency.HIGH:
        print("This is a high urgency task!")

    
    return todo




 


@router.put("/todos/{id}", response_model=ToDoItem,tags=["CRUD"])
async def update_todo(id: UUID, updated_todo: ToDoUpdate):

    todo = find_todo_by_id(id)

    if not todo:
        raise HTTPException(status_code=404, detail="To-do item not found")




    aux = todo.model_copy(update=updated_todo.model_dump())

    todos[todo.id] = aux


    return todos[todo.id] 





@router.delete("/todos/{id}",tags=["CRUD"],status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(id: UUID) -> Response:

    todo = find_todo_by_id(id)

    if not todo:
        raise HTTPException(status_code=404, detail="To-do item not found")

    del todos[todo.id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)

