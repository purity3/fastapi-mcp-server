from fastapi import APIRouter, Request, HTTPException
from starlette.routing import Mount
from typing import Any, Optional
from server import mcp
from auth.credential import verify_api_key
from transport.sse import FastAPISseServerTransport

# 创建路由器
router = APIRouter(tags=["MCP"])

# 创建SSE服务器传输
sse = FastAPISseServerTransport("/messages")

@router.get("/{api_key:path}/sse")
async def handle_sse(
    request: Request, 
    api_key: str
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
        request.scope, request.receive, request._send, path=api_key
    ) as (
        read_stream,
        write_stream,
    ):
        await mcp._mcp_server.run(
            read_stream, write_stream, mcp._mcp_server.create_initialization_options()
        )

# 获取消息挂载点
message_mount = Mount("/messages", app=sse.handle_post_message)

