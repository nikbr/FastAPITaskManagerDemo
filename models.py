from datetime import date
from enum import Enum, auto
from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey, UniqueConstraint, CheckConstraint
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

    task_id: int = Field(
        sa_column=Column(ForeignKey("task.id", ondelete="CASCADE"), primary_key=True)
    )
    related_task_id: int = Field(
        sa_column=Column(ForeignKey("task.id", ondelete="CASCADE"), primary_key=True)
    )

    __table_args__ = (
        UniqueConstraint("task_id", "related_task_id", name="uq_task_relation"),
        CheckConstraint("task_id != related_task_id", name="ck_no_self_relation"),
    )


class Task(TaskBase, table=True):
    __hash__ = object.__hash__
    id: int | None = Field(default=None, primary_key=True)
    user: "User" = Relationship(back_populates="tasks")
    related_tasks: list["Task"] = Relationship(
        link_model=TaskRelation,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskRelation.task_id",
            "secondaryjoin": "Task.id==TaskRelation.related_task_id",
            "collection_class": set,
            "lazy": "selectin",
        },
    )




class UserBase(SQLModel):
    name: str
    role: Role


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tasks: list["Task"] = Relationship(back_populates="user")

