"""
MCP工具相关函数实现
"""
from mcp.server.fastmcp import Context
from utils import mask_api_key

def get_current_sessions(ctx: Context) -> str:
    """
    列出系统中所有活跃的会话
    Args:
        ctx: 上下文对象
    Returns:
        包含所有会话信息的字符串
    """
    result = []

    # 获取session_id和api_key
    if ctx._request_context and ctx._request_context.meta:
        meta = ctx._request_context.meta

        # 添加会话信息
        session_id = getattr(meta, "session_id", None)
        api_key = getattr(meta, "api_key", None)
        
        # 对API密钥进行部分隐藏处理
        masked_api_key = mask_api_key(api_key) if api_key else None

        result.append(f"会话ID: {session_id}")
        result.append(f"API密钥: {masked_api_key}")

    else:
        result.append("无法获取会话信息：meta不可用")

    return "\n".join(result) 