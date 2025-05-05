from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from tools import get_current_sessions
from fastapi import FastAPI
from database.db import services
import logging

# 初始化日志
logger = logging.getLogger(__name__)

# 创建FastMCP服务器
mcp = FastMCP("mcp-server")

# 注册工具函数
mcp.tool()(get_current_sessions)

@asynccontextmanager
async def mcp_lifespan(app: FastAPI):
    """MCP服务器生命周期管理"""
    # 检查会话服务是否已初始化
    if "session_service" not in services:
        logger.warning("未找到会话服务，某些功能可能不可用")
    
    yield

# 该函数可以在 routes/mcp.py 中调用
def get_mcp_app():
    """获取配置好的MCP服务器"""
    return mcp

def get_mcp_transport():
    """获取MCP的传输层"""
    if hasattr(mcp, "_transport"):
        return mcp._transport
    return None

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 直接运行服务器时使用SSE传输
    logger.info("启动MCP服务器")
    mcp.run(transport="sse")