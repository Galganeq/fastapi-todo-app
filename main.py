from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import models
from database import engine, get_db
import schemas
import utils
import oauth2

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


@app.post("/register", response_model=schemas.RegisterOut)
def register_user(new_user: schemas.UserRegister, db: Session = Depends(get_db)):

    if db.query(models.User).filter(models.User.email == new_user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = utils.get_password_hash(new_user.password)

    new_user.password = hashed_password

    new_user = models.User(**new_user.dict())

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = oauth2.create_access_token(data={"user_id": new_user.id})
    return {"token": token}


@app.post("/login", response_model=schemas.LoginOut)
def log_in_user(user: schemas.UserLogin, db: Session = Depends(get_db)):

    choosen_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not choosen_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    if not utils.authenticate_user(user.password, choosen_user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials"
        )

    token = oauth2.create_access_token(data={"user_id": choosen_user.id})
    return {"token": token}


@app.post("/todos", response_model=schemas.TaskOut)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):

    new_task = models.Task(owner_id=current_user.id, **task.dict())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.put("/todos/{id}", response_model=schemas.UpdateTaskOut)
def update_task(
    id: int,
    updated_task: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):

    choosen_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not choosen_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task does not exist"
        )

    if choosen_task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    choosen_task.title = updated_task.title
    choosen_task.description = updated_task.description
    db.commit()
    db.refresh(choosen_task)

    return choosen_task


@app.delete("/todos/{id}")
def delete_task(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    task_to_delete = db.query(models.Task).filter(models.Task.id == id).first()

    if not task_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task_to_delete.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    db.delete(task_to_delete)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/todos", response_model=schemas.GetTasksOut)
def show_tasks(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
    limit: int = 10,
    page: int = 1,
):

    total = db.query(models.Task).count()
    tasks = db.query(models.Task).limit(limit).offset((page - 1) * limit).all()

    return {"data": tasks, "page": page, "limit": limit, "total": total}
