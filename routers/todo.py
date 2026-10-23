from fastapi import APIRouter,Query,HTTPException,Response,status,Depends
from typing import Annotated, Optional
import uuid
from uuid import UUID
from pydantic import AfterValidator
from dependencies import check_todo_data,Pagination,find_todo_by_id,get_current_active_user,ActiveUserDep,FindToDoByIdDep,FindUserToDoByIdDep,ValidateToDoDep,GetUserToDosWithPaginationDep
from database.db import todos,SessionDep


from models.todoModels import Urgency, ToDoBase,ToDoCreate,ToDoUpdate,ToDoItem
from models.loginModels import User,UserInDB
from sqlmodel import select
from auth import get_user


# router = APIRouter(prefix="/todos",dependencies=[Depends(get_current_active_user)])

router = APIRouter(prefix="/todos")


forbidden_tasks = ["drink", "smoke", "gamble","drugs"]




@router.post("/",tags=["CRUD"],status_code=status.HTTP_201_CREATED)
async def create_todo(todo: ValidateToDoDep,session:SessionDep,user:ActiveUserDep,response:Response) -> ToDoItem:


    todoItem = ToDoItem.model_validate(todo)


# implement helper function for below

    user.todos.append(todoItem)

    session.add(user)
    session.commit()
    session.refresh(todoItem)

    
    response.headers["Location"] = f"/todos/{todoItem.id}"

    return todoItem





@router.get("/",response_model=list[ToDoItem],tags=["CRUD"])
async def get_all_todos(todos:GetUserToDosWithPaginationDep):

   
    # user_todos = session.exec(select(ToDoItem).where(ToDoItem.user_id == user.id).offset(pagination.skip).limit(pagination.limit)).all()
   

    return todos


    
@router.get("/{id}",response_model=ToDoItem,tags=["CRUD"])
async def get_todo(todo:FindUserToDoByIdDep):

    # todo = find_todo_by_id(id)

    # if not todo:
    #     raise HTTPException(status_code=404, detail="To-do item not found")

    # if todo.urgency == Urgency.HIGH:
    #     print("This is a high urgency task!")



    # if todo.user_id != user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Forbidden from accessing this item!")

    
    return todo




# @router.get("/{id}",response_model=ToDoItem,tags=["CRUD"])
# async def get_todo(todo:FindToDoByIdDep,session:SessionDep,user:ActiveUserDep):

#     # todo = find_todo_by_id(id)

#     # if not todo:
#     #     raise HTTPException(status_code=404, detail="To-do item not found")

#     # if todo.urgency == Urgency.HIGH:
#     #     print("This is a high urgency task!")



#     if todo.user_id != user.id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Forbidden from accessing this item!")

    
#     return todo




 


@router.patch("/{id}", response_model=ToDoItem,tags=["CRUD"])
async def update_todo(updated_todo: ToDoUpdate, todo:FindUserToDoByIdDep,session:SessionDep,user:ActiveUserDep):


    
    todo.sqlmodel_update(updated_todo.model_dump(exclude_unset=True))
    session.add(todo)
    session.commit()
    session.refresh(todo)
  

    return todo





@router.delete("/{id}",tags=["CRUD"],status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo:FindToDoByIdDep,user:ActiveUserDep,session:SessionDep) -> Response:


    session.delete(todo)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)







    

# @router.post("/",tags=["CRUD"])
# async def create_todo(todo: Annotated[ToDoCreate,Depends(check_todo_data)],response:Response) -> ToDoItem:

#     #generate a random id for the new to-do item
#     new_id = uuid.uuid4()

#     todoItem = ToDoItem(id=new_id, **todo.model_dump())

#     todos[new_id] = todoItem

    
#     response.headers["Location"] = f"/todos/{new_id}"

#     return todoItem





# @router.get("/",response_model=list[ToDoItem],tags=["CRUD"])
# async def get_all_todos(pagination:Annotated[Pagination,Depends()]):

    
#     return list(todos.values())[pagination.skip:pagination.skip+pagination.limit]




# @router.get("/{id}",response_model=ToDoItem,tags=["CRUD"])
# async def get_todo(id: UUID):

#     todo = find_todo_by_id(id)

#     if not todo:
#         raise HTTPException(status_code=404, detail="To-do item not found")

#     if todo.urgency == Urgency.HIGH:
#         print("This is a high urgency task!")

    
#     return todo




 


# @router.put("/{id}", response_model=ToDoItem,tags=["CRUD"])
# async def update_todo(updated_todo: ToDoUpdate, dbToDo:Annotated[ToDoItem,Depends(find_todo_by_id)]):

#     aux = dbToDo.model_copy(update=updated_todo.model_dump())

#     todos[dbToDo.id] = aux


#     return todos[dbToDo.id] 





# @router.delete("/{id}",tags=["CRUD"],status_code=status.HTTP_204_NO_CONTENT)
# async def delete_todo(dbToDo:Annotated[ToDoItem,Depends(find_todo_by_id)]) -> Response:


#     del todos[dbToDo.id]

#     return Response(status_code=status.HTTP_204_NO_CONTENT)

