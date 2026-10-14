
from enum import Enum
from pydantic import BaseModel,Field
from typing import Optional
from uuid import UUID


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


