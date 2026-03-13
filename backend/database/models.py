from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from .db import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium") # low, medium, high
    status = Column(String, default="pending") # pending, completed
    due_date = Column(DateTime(timezone=True), nullable=True)
    reminder_time = Column(DateTime(timezone=True), nullable=True)
    tags = Column(String, nullable=True) # Comma separated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Keep is_completed for backward compat or sync it with status
    is_completed = Column(Boolean, default=False)

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    linked_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    progress = Column(Integer, default=0) # 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmailContact(Base):
    __tablename__ = "email_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # Future multi-user support
    nickname = Column(String, unique=True, index=True, nullable=False) # "Ravi", "Mom"
    email = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    contact_id = Column(Integer, ForeignKey("email_contacts.id"), nullable=True)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    encrypted_body = Column(Text, nullable=True) # We will store encrypted body if needed, or just status
    status = Column(String, default="PENDING") # SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    message_id = Column(String, nullable=True) # Gmail Message ID
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
