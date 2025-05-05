from mcp.server.fastmcp import FastMCP
from tools import get_current_sessions

mcp = FastMCP("mcp-server")

# 注册工具函数
mcp.tool()(get_current_sessions)

if __name__ == "__main__":
    mcp.run(transport="sse")