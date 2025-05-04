from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class JsonRpcMeta(BaseModel):
    """
    JSON-RPC 请求的元数据
    """
    session_id: Optional[str] = None
    path: Optional[str] = None


class JsonRpcParams(BaseModel):
    """
    JSON-RPC 请求的参数
    """
    meta: Optional[JsonRpcMeta] = Field(default_factory=JsonRpcMeta, alias="_meta")
    # 其他参数可以是任意类型
    extra_fields: Dict[str, Any] = Field(default_factory=dict)


class JsonRpcRequest(BaseModel):
    """
    JSON-RPC 请求对象
    """
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[JsonRpcParams] = None
