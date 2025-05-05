from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Generator

from database.db import SessionLocal
from services.session import SessionService

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    使用示例:
    ```
    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        ...
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """
    获取会话管理服务
    
    使用示例:
    ```
    @app.get("/sessions")
    def read_sessions(service: SessionService = Depends(get_session_service)):
        ...
    ```
    """
    return SessionService(db) 