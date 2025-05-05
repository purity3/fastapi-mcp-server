from fastapi import FastAPI, Request
import logging
from contextlib import asynccontextmanager

# 导入路由模块
from config import HOST, PORT
from database.db import init_db, get_db, services
from services.session import SessionService
from routes import main_router

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化应用
    logger.info("启动应用...")
    
    # 初始化数据库和服务
    init_db()
    db = next(get_db())
    services["session_service"] = SessionService(db)
    
    # 导入MCP相关组件
    from server import mcp_lifespan
    # 执行MCP生命周期初始化
    async with mcp_lifespan(app):
        # yield控制权返回给FastAPI
        yield
    
    # 应用关闭时清理资源
    if "session_service" in services:
        services["session_service"].db.close()
    services.clear()
    logger.info("应用已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="FastAPI MCP SSE",
    description="A demonstration of Server-Sent Events with Model Context "
    "Protocol integration",
    version="0.1.0",
    lifespan=lifespan,
)

# 包含所有路由
app.include_router(main_router)

# 挂载MCP
from routes.mcp import message_mount
app.router.routes.append(message_mount)

def main():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
