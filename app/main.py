from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, auth
from .database import SessionLocal, engine, Base

# -------------------------
# Create database tables
# -------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Professional Todo App")
templates = Jinja2Templates(directory="app/templates")

# -------------------------
# OAuth2 scheme
# -------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# -------------------------
# Dependency: DB session
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Helper: Get current user
# -------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = auth.decode_token(token)
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# -------------------------
# HTML Homepage
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------
# Auth Routes
# -------------------------
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = models.User(
        username=user.username,
        hashed_password=auth.hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# -------------------------
# Todo Routes
# -------------------------
@app.post("/todos", response_model=schemas.TodoResponse)
def create_todo(
    todo: schemas.TodoCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_todo = models.Todo(**todo.dict(), owner_id=current_user.id)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@app.get("/todos", response_model=List[schemas.TodoResponse])
def get_todos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Todo).filter(models.Todo.owner_id == current_user.id).all()

@app.put("/todos/{todo_id}", response_model=schemas.TodoResponse)
def update_todo(
    todo_id: int,
    todo: schemas.TodoUpdate,  # <- uses new update schema
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id,
        models.Todo.owner_id == current_user.id
    ).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Update only provided fields
    if todo.title is not None:
        db_todo.title = todo.title
    if todo.description is not None:
        db_todo.description = todo.description
    if todo.completed is not None:
        db_todo.completed = todo.completed

    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id,
        models.Todo.owner_id == current_user.id
    ).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted"}
