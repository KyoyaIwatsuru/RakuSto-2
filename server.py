from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime, timedelta

#create FastAPI instance
app = FastAPI()

# create database
DATABASE_URL = "sqlite:///./InternDatabase.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# define the database's data model
class User(Base):
    __tablename__ = 'users'
    UserId = Column(Integer, primary_key=True, autoincrement=True)
    UserName = Column(String, nullable=True)
    Password = Column(String, nullable=True)
    stocks = relationship("Stock", back_populates="user")

class Item(Base):
    __tablename__ = 'items'
    ItemId = Column(Integer, primary_key=True, autoincrement=True)
    ItemName = Column(String, nullable=True)
    Category = Column(String, nullable=True)
    PurchaseDate = Column(Date, nullable=True)
    LimitDate = Column(Date, nullable=True)
    Unit = Column(Integer, nullable=True)
    stocks = relationship("Stock", back_populates="item")

class Stock(Base):
    __tablename__ = 'stocks'
    StockId = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey('users.UserId'), nullable=True)
    ItemId = Column(Integer, ForeignKey('items.ItemId'), nullable=True)
    user = relationship("User", back_populates="stocks")
    item = relationship("Item", back_populates="stocks")

class Recipe(Base):
    __tablename__ = 'recipes'
    RecipeId = Column(Integer, primary_key=True, autoincrement=True)
    RecipeTitle = Column(String, nullable=True)
    RecipeCategory = Column(String, nullable=True)
    RecipeURL = Column(String, nullable=True)

# create the table 
Base.metadata.create_all(bind=engine)

# Pydantic Model,this can validate the data from API
class UserCreate(BaseModel):
    UserName: str
    Password: str

class ItemCreate(BaseModel):
    ItemName: str
    Category: str
    PurchaseDate: datetime
    LimitDate: datetime
    Unit: int

class StockCreate(BaseModel):
    UserId: int
    ItemId: int


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
    Category: str
    PurchaseDate: datetime
    LimitDate: datetime
    Unit: int

    class Config:
        orm_mode = True
        from_attributes = True

class StockRead(BaseModel):
    StockId: int
    UserId: int
    ItemId: int

    class Config:
        orm_mode = True
        from_attributes = True

class UserStocksItems(BaseModel):
    StockId: int
    Item: ItemRead

    class Config:
        orm_mode = True
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/items/", response_model=ItemCreate)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/stocks/", response_model=StockCreate)
def create_stock(stock: StockCreate, db: Session = Depends(get_db)):
    db_stock = Stock(**stock.model_dump())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock
@app.get("/users/", response_model=list[UserRead])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/items/", response_model=list[ItemRead])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@app.get("/stocks/", response_model=list[StockRead])
def read_stocks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    stocks = db.query(Stock).offset(skip).limit(limit).all()
    return stocks

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

@app.get("/stocks/{stock_id}", response_model=StockRead)
def read_stock(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.StockId == stock_id).first()
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock
@app.get("/users/{user_id}/stocks-items", response_model=list[UserStocksItems])
def read_user_stocks_items(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserId == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    stocks = db.query(Stock).filter(Stock.UserId == user_id).all()
    results = []
    for stock in stocks:
        item = db.query(Item).filter(Item.ItemId == stock.ItemId).first()
        results.append(UserStocksItems(StockId=stock.StockId, Item=ItemRead.model_validate(item)))
    return results
# 启动命令（放在命令行中运行）
# uvicorn your_script_name:app --reload 