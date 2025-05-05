from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from contextlib import contextmanager
import os
from pathlib import Path
from config import DATABASE_URL
from typing import Generator, Dict, Any

# 全局服务容器
services: Dict[str, Any] = {}

# 数据库基类
Base: DeclarativeMeta = declarative_base()

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    获取数据库会话的生成器函数
    
    使用示例:
    ```
    db = next(get_db())
    # 或者
    for db in get_db():
        # 使用 db...
        break
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    数据库会话上下文管理器
    
    使用示例:
    ```
    with get_db_context() as db:
        db.query(...)
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine) 