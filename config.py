import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# API验证配置
API_URL = os.getenv("API_URL", "http://deepuml.xhus.cn")
API_KEY_PREFIX = os.getenv("API_KEY_PREFIX", "sa_tools_") 