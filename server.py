from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("mcp-server")

@mcp.tool()
def basic_search(query: str):
    """基本搜索功能（自动注册失败时的后备工具）"""
    return f"基本搜索结果: {query}"

@mcp.tool()
def list_all_sessions(ctx: Context) -> str:
    """
    列出系统中所有活跃的会话
    Args:
        ctx: 上下文对象
    Returns:
        包含所有会话信息的字符串
    """
    result = []

    # 获取session_id和path
    if ctx._request_context and ctx._request_context.meta:
        meta = ctx._request_context.meta

        # 添加会话信息
        session_id = getattr(meta, "session_id", None)
        path = getattr(meta, "path", None)

        result.append(f"会话ID: {session_id}")
        result.append(f"路径: {path}")

    else:
        result.append("无法获取会话信息：meta不可用")

    return "\n".join(result)

if __name__ == "__main__":
    mcp.run(transport="sse")