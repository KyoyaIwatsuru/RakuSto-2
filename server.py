from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import csv

# Create FastAPI instance
app = FastAPI()

# Create database
DATABASE_URL = "sqlite:///./InternDatabase.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the database's data model
class User(Base):
    __tablename__ = 'users'
    UserId = Column(Integer, primary_key=True, autoincrement=True)
    UserName = Column(String, nullable=True)
    Password = Column(String, nullable=True)
    items = relationship("Item", back_populates="user")

class Item(Base):
    __tablename__ = 'items'
    ItemId = Column(Integer, primary_key=True, autoincrement=True)
    ItemName = Column(String, nullable=True)
    ItemImage = Column(String, nullable=True)
    Category = Column(String, nullable=True)
    PurchaseDate = Column(Date, nullable=True)
    LimitDate = Column(Date, nullable=True)
    Unit = Column(Integer, nullable=True)
    ItemURL = Column(String, nullable=True)
    UserId = Column(Integer, ForeignKey('users.UserId'), nullable=False)
    user = relationship("User", back_populates="items")

class Recipe(Base):
    __tablename__ = 'recipes'
    RecipeId = Column(Integer, primary_key=True, autoincrement=True)
    RecipeTitle = Column(String, nullable=True)
    RecipeCategory = Column(String, nullable=True)
    RecipeImageURL = Column(String, nullable=True)
    RecipeURL = Column(String, nullable=True)

# Create the table 
Base.metadata.create_all(bind=engine)

# Pydantic Model, this can validate the data from API
class UserCreate(BaseModel):
    UserName: str
    Password: str

class ItemCreate(BaseModel):
    ItemName: str
    ItemImage: str
    Category: str
    PurchaseDate: datetime
    LimitDate: datetime
    Unit: int
    ItemURL: str
    UserId: int

class RecipeCreate(BaseModel):
    RecipeTitle: str
    RecipeCategory: str
    RecipeURL: str

class UserRead(BaseModel):
    UserId: int
    UserName: str
    Password: str

    class Config:
        orm_mode = True
        from_attributes = True

class ItemRead(BaseModel):
    ItemId: int
    ItemName: str
    ItemImage: str
    Category: str
    PurchaseDate: datetime
    LimitDate: datetime
    Unit: int
    ItemURL: str
    UserId: int

    class Config:
        orm_mode = True
        from_attributes = True

class RecipeRead(BaseModel):
    RecipeId: int
    RecipeTitle: str
    RecipeCategory: str
    RecipeURL: str
    RecipeImageURL: str

    class Config:
        orm_mode = True
        from_attributes = True

class UserItems(BaseModel):
    ItemId: int
    ItemName: str
    Category: str
    PurchaseDate: datetime
    LimitDate: datetime
    Unit: int
    ItemURL: str

    class Config:
        orm_mode = True
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database with CSV data
def init_db():
    db = SessionLocal()
    try:
        with open('recipes.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                recipe = Recipe(
                    RecipeTitle=row['title'],
                    RecipeCategory=row['parent_category'],
                    RecipeURL=row['link'],
                    RecipeImageURL=row['image_url']
                )
                db.add(recipe)
            db.commit()
    finally:
        db.close()

# Initialize database with CSV data when FastAPI starts
@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/items/", response_model=ItemRead)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/users/{user_id}/items/", response_model=ItemRead)
def add_item_to_user(user_id: int, item: ItemCreate = Body(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.UserId == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_item = Item(**item.dict(), UserId=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/users/", response_model=list[UserRead])
def read_users(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/items/", response_model=list[ItemRead])
def read_items(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@app.get("/recipes/", response_model=list[RecipeRead])
def read_recipes(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    recipes = db.query(Recipe).offset(skip).limit(limit).all()
    return recipes

@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserId == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/items/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.ItemId == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/users/{user_id}/items", response_model=list[UserItems])
def read_user_items(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserId == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    items = user.items
    return items

# 启动命令（放在命令行中运行）
# uvicorn your_script_name:app --reload