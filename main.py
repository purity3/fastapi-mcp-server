from fastapi import FastAPI, Request
import logging

# 导入路由模块
from config import HOST, PORT
from routes.mcp import router as mcp_router, message_mount
from database.db import init_db

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="FastAPI MCP SSE",
    description="A demonstration of Server-Sent Events with Model Context "
    "Protocol integration",
    version="0.1.0",
)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    logger.info("初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

# 包含MCP路由
app.include_router(mcp_router)

# 添加消息挂载点
app.router.routes.append(message_mount)

@app.get("/")
async def root():
    return {"message": "Hello World"}

def main():
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
