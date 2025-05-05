from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Session(BaseModel):
    """会话模型"""
    session_id: str
    api_key: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
