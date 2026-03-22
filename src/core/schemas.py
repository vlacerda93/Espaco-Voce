from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class JournalEntry(BaseModel):
    content: str = Field(..., min_length=1)
    mood: str = Field(default="Neutro")

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    cognitive_load: int = Field(..., ge=1, le=5)
    deadline: Optional[datetime] = None

class MetricUpdate(BaseModel):
    metric_type: str
    value: float
