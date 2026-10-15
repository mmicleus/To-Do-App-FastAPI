
from enum import Enum
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from sqlmodel import Field,SQLModel



class Urgency(str,Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"



class ToDoBase(SQLModel):
    title: str = Field(index=True,description="Title of the to-do item", min_length=1, max_length=20)
    description: Optional[str] = Field(default=None, description="Description of the to-do item", max_length=50)
    completed: bool = False
    urgency: Urgency = Urgency.LOW


class ToDoItem(ToDoBase, table=True):
    id: int | None = Field(default=None,primary_key=True)



class ToDoCreate(ToDoBase):
    pass

class ToDoUpdate(SQLModel):
    title: str| None = Field(default=None,description="Title of the to-do item", min_length=1, max_length=20)
    description: str| None = Field(default=None,description="Description of the to-do item", max_length=50)
    completed: bool | None = None
    urgency: Urgency | None = None












