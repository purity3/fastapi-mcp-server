# 路由模块初始化文件
# 这个文件使routes目录成为一个Python包

from fastapi import APIRouter

# 创建主路由
main_router = APIRouter()

# 导入其他路由模块
from routes.mcp import router as mcp_router

# 包含其他路由模块
main_router.include_router(mcp_router)
