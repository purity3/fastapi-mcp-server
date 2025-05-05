from fastapi import APIRouter, Request, HTTPException, Depends
from starlette.routing import Mount
from typing import Any, Optional, List
from server import mcp, get_mcp_app, get_mcp_transport
from auth.credential import verify_api_key
from transport.sse import FastAPISseServerTransport
from services.session import SessionService
from database.db import services
import logging

# 初始化日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(tags=["MCP"])

# 获取MCP应用
mcp_app = get_mcp_app()

# 获取MCP传输
mcp_transport = get_mcp_transport()

# 如果MCP传输不存在，创建新的SSE传输
if not mcp_transport or not isinstance(mcp_transport, FastAPISseServerTransport):
    sse = FastAPISseServerTransport("/messages")
else:
    sse = mcp_transport

@router.get("/{api_key:path}/sse")
async def handle_sse(
    request: Request,
    api_key: str,
):
    """
    处理SSE连接请求

    Args:
        request: FastAPI请求对象
        api_key: API密钥（作为路径参数）

    Returns:
        SSE响应
    """
    # 如果没有提供API密钥，返回错误
    if not api_key:
        raise HTTPException(status_code=401, detail="未提供API密钥")

    # 验证API密钥
    is_valid = await verify_api_key(api_key)
    if not is_valid:
        raise HTTPException(status_code=401, detail="API密钥无效")

    # API密钥验证通过，建立SSE连接
    async with sse.connect_sse(
        request.scope, request.receive, request._send, api_key=api_key
    ) as (
        read_stream,
        write_stream,
    ):
        await mcp_app._mcp_server.run(
            read_stream, write_stream, mcp_app._mcp_server.create_initialization_options()
        )

# 获取消息挂载点
message_mount = Mount("/messages", app=sse.handle_post_message)
