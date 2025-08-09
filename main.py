from fastapi import FastAPI, Query, Request, Depends, Path, HTTPException, Body
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from db import init_db, get_session, engine
from models import Role, Priority, Status, TaskType, TaskBase,  Task, UserBase, User
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import date, timedelta
import random

class TaskQueryParams(BaseModel):
    contains: str | None = None
    status : Status | None = None
    priority : int | None = None
    type : TaskType | None = None

class TaskUpdateParams(BaseModel):
    name: str | None = None
    description: str|None = None
    due_date : str | None = None
    status : Status | None = None
    priority : Priority | None = None
    type : TaskType | None = None
    user_id: int | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        create_users(session)
        seed_tasks(session)
    yield


def seed_tasks(session: Session, count: int = 40) -> None:
    task_list = session.exec(select(Task)).all()
    if task_list:
        return
    
    users = session.exec(select(User)).all()

    allowed_types = {
        Role.MANAGER: [TaskType.MANAGING, TaskType.REVIEW],
        Role.SENIOR: [TaskType.CODING, TaskType.REVIEW],
        Role.JUNIOR: [TaskType.CODING, TaskType.TESTING],
        Role.TESTER: [TaskType.TESTING, TaskType.TESTING]
    }

    priorities = [p.value for p in Priority]
    statuses = [s for s in Status if s is not Status.OVERDUE]

    tasks: list[Task] = []
    for user in users:
        types = allowed_types[user.role]
        types = [types[0],types[1]]
    
        for idx, ttype in enumerate(types, start=1):
        # Due date: within next 30 days (no overdue for this seeding)
            due_date = date.today() + timedelta(days=random.randint(1, 30))

            status = random.choice(statuses)
            priority = random.choice(priorities)

            task = Task(
                name=f"{ttype.value.capitalize()} task for {user.name} #{idx}",
                description=f"Assigned {ttype.value} task to {user.name} ({user.role.value})",
                due_date=due_date,
                status=status,
                priority=priority,
                type=ttype,
                user_id=user.id,
            )
            tasks.append(task)

    session.add_all(tasks)
    session.commit()




def create_users(session:Session) -> None:
    user_list = session.exec(select(User)).all()
    if not user_list:
        names = [
            "Aiden", "Sophia", "Liam", "Olivia", "Noah",
            "Emma", "Ethan", "Ava", "Mason", "Isabella",
            "Logan", "Mia", "Lucas", "Charlotte", "Elijah",
            "Amelia", "James", "Harper", "Benjamin", "Evelyn"
        ]

        role_distribution = [
            (Role.MANAGER, 2),
            (Role.SENIOR, 4),
            (Role.JUNIOR, 8),
            (Role.TESTER, 6),
        ]

        users = []
        i = 0

        for role, count in role_distribution:
            for _ in range(count):
                users.append(User(name=names[i], role=role))
                i+=1

        session.add_all(users)
        session.commit()



app = FastAPI(lifespan = lifespan)

@app.get("/")
async def index() -> str:
    return "Task Manager API"

@app.get('/users')
async def users(
    role : Role | None = None,
    session: Session = Depends(get_session)
    ) -> list[User]:
    user_list = session.exec(select(User)).all()
    if role:
        user_list = [
            u for u in user_list if role == u.role
        ]

    return user_list


@app.get('/users/{user_id}')
async def user(
    user_id:Annotated[int, Path(title="User ID")],
    session: Session = Depends(get_session)
    ) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get('/users/role/{user_role}')
async def users_by_role(
    user_role:Annotated[Role, Path(title="User Role")],
    session: Session = Depends(get_session)
    ) -> list[User]:
    user_list = session.exec(
        select(User).where(User.role==user_role)
    ).all()
    return user_list

@app.get('/tasks')
async def tasks(
    filter_query: Annotated[TaskQueryParams, Query(title="Filter tasks by contains, status, priority and type.")],
    session: Session = Depends(get_session)
    ) -> list[Task]:
    #TODO add query param validation
    #TODO fix Priority param
    task_list = session.exec(select(Task)).all()
    print(filter_query)
    contains = filter_query.contains
    priority = filter_query.priority
    status = filter_query.status
    type = filter_query.type

    if contains:
        task_list = [
            t for t in task_list if contains in t.name or contains in t.description
        ]
    if priority:
        task_list = [
            t for t in task_list if t.priority==int(priority)
        ]
    if status:
        task_list = [
            t for t in task_list if str(t.status).lower()==str(status).lower()
        ]

    if type:
        task_list = [
            t for t in task_list if str(t.type).lower()==str(type).lower()
        ]


    return task_list


@app.get('/tasks/{task_id}')
async def task(
    task_id: Annotated[int, Path(title="Task ID")],
    session: Session = Depends(get_session)
    ) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get('/tasks/priority/{priority}')
async def tasks_by_priority(
    priority:Annotated[int, Path(title="Task priority")], #TODO need to make this Priority in the future probably
    session: Session = Depends(get_session)
    ) -> list[Task]:
    task_list = session.exec(
        select(Task).where(Task.priority==int(priority))
    ).all()
    return task_list

@app.get('/tasks/status/{status}')
async def tasks_by_status(
    status:Annotated[Status, Path(title="Task status")],
    session: Session = Depends(get_session)
    ) -> list[Task]:
    task_list = session.exec(
        select(Task).where(Task.status==status)
    ).all()
    return task_list

@app.get('/tasks/type/{type}')
async def tasks_by_type(
    type:Annotated[TaskType, Path(title="Task type")],
    session: Session = Depends(get_session)
    ) -> list[Task]:
    task_list = session.exec(
        select(Task).where(Task.type==type)
    ).all()
    return task_list


@app.put('/tasks/{task_id}')
async def update_task(
    task_id:Annotated[int, Path(title="Task ID")],
    update: TaskUpdateParams = Body(..., description="Any subset of task fields"),
    session: Session = Depends(get_session)
    ) -> Task:
    
    task = session.get(Task, task_id)
    if not task_id:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = update.model_dump(exclude_unset=True, exclude_none=True)
    new_name = update_data.get("name")
    new_desc = update_data.get("description")
    new_due_date = update_data.get("due_date")
    new_status = update_data.get("status")
    new_priority = update_data.get("priority")
    new_type = update_data.get("type")
    new_user_id = update_data.get("user_id")
    
    if new_name: task.name = new_name
    if new_desc: task.description = new_desc
    if new_due_date: task.due_date = date(new_due_date)
    if new_status: task.status = new_status
    if new_priority: task.priority = new_priority.value
    if new_type: task.type = new_type
    if new_user_id: task.user_id = new_user_id
    
    session.add(task)
    session.commit()
    session.refresh(task)

    return task

@app.delete('/tasks/{task_id}')
async def delete_task(
    task_id:Annotated[int, Path(title="Task ID")],
    session: Session = Depends(get_session)
                      ) -> Task:
    task = session.get(Task, task_id)
    if not task_id:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return task

@app.post('/tasks')
async def add_task(
    task_data : TaskBase,
    session: Session = Depends(get_session)
                   ) -> Task:
    new_task = Task(name=task_data.name,
                   description=task_data.description,
                   due_date=task_data.due_date,
                   status=task_data.status,
                   priority=task_data.priority,
                   type=task_data.type,
                   user_id=task_data.user_id)
    #TODO: add validation to check if user id exists
    #TODO: add validation for user role vs task type

    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task
