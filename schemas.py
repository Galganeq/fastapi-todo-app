from pydantic import BaseModel
from typing import Optional, List


class User(BaseModel):
    email: str
    password: str


class UserRegister(User):
    name: str


class UserLogin(User):
    pass


class Task(BaseModel):
    title: str
    description: str


class TaskCreate(Task):
    pass


class TaskOut(Task):
    id: int


class TaskUpdate(Task):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):

    id: Optional[int] = None


class RegisterOut(BaseModel):
    token: str


class LoginOut(RegisterOut):
    pass


class TaskOut(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True


class UpdateTaskOut(TaskOut):
    pass


class GetTasksOut(BaseModel):

    data: List[TaskOut]
    page: int
    limit: int
    total: int
