from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text
from database import Base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

UTC_PLUS_7 = timezone(timedelta(hours=7))

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    user_password = Column(String, nullable=False)
    
    recipes = relationship("Reciept", back_populates="user")

class Reciept(Base):
    __tablename__ = "recipe"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    recipe_name = Column(String, nullable=False)
    image = Column(LargeBinary, nullable=False)
    detail = Column(Text, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(UTC_PLUS_7))
    
    user = relationship("User", back_populates="recipes")

class User_signup(BaseModel):
    name: str
    username: str
    password: str

    class Config:
        orm_mode = True  # ให้ Pydantic เข้าใจว่าใช้กับ SQLAlchemy model

class User_login(BaseModel):
    username: str
    password: str

    class Config:
        orm_mode = True