from datetime import date
from enum import Enum, auto
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    OVERDUE = "overdue"

class Priority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

class Role(Enum):
    MANAGER = "manager"
    SENIOR = "senior"
    JUNIOR = "junior"
    TESTER = "tester"

class TaskType(Enum):
    CODING = "coding"
    REVIEW = "review"
    TESTING = "testing"
    MANAGING = "managing"

class TaskBase(SQLModel):
    name: str
    description: str
    due_date: date
    status: Status
    priority: int
    type: TaskType
    user_id: int | None = Field(default = None, foreign_key="user.id")

class TaskRelation(SQLModel, table=True):
    task_id: int |None = Field(foreign_key="task.id", primary_key=True)
    related_task_id : int | None= Field(foreign_key="task.id", primary_key=True)

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: "User" = Relationship(back_populates="tasks")
    relatedTasks: list["Task"] = Relationship(
        back_populates="relatedTo",
        link_model=TaskRelation,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskRelation.task_id",
            "secondaryjoin": "Task.id==TaskRelation.related_task_id",
        },
    )

    relatedTo: list["Task"] = Relationship(
        back_populates="relatedTasks",
        link_model=TaskRelation,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskRelation.related_task_id",
            "secondaryjoin": "Task.id==TaskRelation.task_id",
        },
    )

class UserBase(SQLModel):
    name: str
    role: Role


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tasks: list["Task"] = Relationship(back_populates="user")

