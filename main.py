from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os

# 导入路由模块
from config import HOST, PORT
from routes.mcp import router as mcp_router, message_mount

# 创建FastAPI应用
app = FastAPI(
    title="FastAPI MCP SSE",
    description="A demonstration of Server-Sent Events with Model Context "
    "Protocol integration",
    version="0.1.0",
)

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
