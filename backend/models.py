from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String, unique=True, index=True)
    display_name = Column(String)
    
    files = relationship("File", back_populates="owner")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_type = Column(String) # pdf, image
    storage_path = Column(String)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="files")
    tags = relationship("Tag", back_populates="file")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    
    file = relationship("File", back_populates="tags")
