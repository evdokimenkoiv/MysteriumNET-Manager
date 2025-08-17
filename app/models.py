from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime

class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    wallet: Optional[str] = None
    host: Optional[str] = None
    version: Optional[str] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=False)))
