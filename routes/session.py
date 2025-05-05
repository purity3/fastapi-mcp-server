from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any
from database.db import services
from services.session import SessionService

# 创建路由器
router = APIRouter(tags=["Session"])


@router.get("/")
async def root(request: Request):
    # 获取应用实例
    app = request.app

    # 获取服务状态
    status = "normal" if "session_service" in services else "not started"
    
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "status": status,
    }
