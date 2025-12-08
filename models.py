from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

engine = create_engine("sqlite:///smartpass.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    unique_id = Column(String, unique=True, index=True, nullable=False)
    qr_code_path = Column(String, nullable=False)
    last_checkin = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    logs = relationship("CheckLog", back_populates="user")
    
class CheckLog(Base):
     __tablename__ = "check_logs"
     id = Column(Integer, primary_key=True)
     user_id = Column(Integer, ForeignKey("users.id"))
     action = Column(String)
     timestamp = Column(DateTime, default=datetime.utcnow)
     
     user = relationship("User", back_populates="logs")

def init_db():
    Base.metadata.create_all(engine)
