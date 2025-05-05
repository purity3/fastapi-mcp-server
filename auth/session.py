import os
from auth.credential import verify_api_key
import secrets
import sqlite3

def create_session(api_key: str, session_id: str) -> str:
    """
    创建新的会话
    
    Args:
    """
    if not verify_api_key(api_key):
        raise ValueError("Invalid API key")
    
    session_id = secrets.token_hex(16)
    return session_id

