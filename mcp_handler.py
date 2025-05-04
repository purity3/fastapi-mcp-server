from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-server")

@mcp.tool()
def basic_search(query: str):
    """基本搜索功能（自动注册失败时的后备工具）"""
    return f"基本搜索结果: {query}"

if __name__ == "__main__":
    mcp.run(transport="sse")