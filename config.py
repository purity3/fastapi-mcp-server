import os
from dotenv import load_dotenv
from pathlib import Path

# 加载.env文件
load_dotenv()

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# API验证配置
API_URL = os.getenv("API_URL", "http://deepuml.xhus.cn")
API_KEY_PREFIX = os.getenv("API_KEY_PREFIX", "sa_tools_") 

# 数据库配置
DB_PATH = os.getenv("DB_PATH", Path(__file__).parent / "database" / "session.db")
DATABASE_URL = f"sqlite:///{DB_PATH}" 