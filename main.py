from fastapi import FastAPI, Request
from mcp.server.fastmcp import FastMCP, Context
from starlette.routing import Mount
from transport.sse import FastAPISseServerTransport
from dotenv import load_dotenv
import os


mcp = FastMCP("mcp-server")
app = FastAPI(
    title="FastAPI MCP SSE",
    description="A demonstration of Server-Sent Events with Model Context "
    "Protocol integration",
    version="0.1.0",
)

sse = FastAPISseServerTransport("/messages")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/{path:path}/sse", tags=["MCP"])
async def handle_sse(request: Request, path: str):
    print("path", path)
    async with sse.connect_sse(
        request.scope, request.receive, request._send, path=path
    ) as (
        read_stream,
        write_stream,
    ):
        await mcp._mcp_server.run(
            read_stream, write_stream, mcp._mcp_server.create_initialization_options()
        )


app.router.routes.append(Mount("/messages", app=sse.handle_post_message))


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


load_dotenv()


def main():
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", 8000)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
