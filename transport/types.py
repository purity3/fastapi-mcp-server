from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, model_validator


class JsonRpcMeta(BaseModel):
    """
    JSON-RPC 请求的元数据
    """
    session_id: Optional[str] = None
    api_key: Optional[str] = None


class JsonRpcParams(BaseModel):
    """
    JSON-RPC 请求的参数
    """
    meta: Optional[JsonRpcMeta] = Field(default_factory=JsonRpcMeta, alias="_meta")
    
    # 允许模型接受任何额外字段
    model_config = {
        "extra": "allow",
    }
    
    @model_validator(mode="before")
    @classmethod
    def extract_meta(cls, data):
        """提取元数据，保留其他所有原始字段"""
        if isinstance(data, dict):
            # 确保元数据不丢失
            if "_meta" not in data:
                data["_meta"] = {}
        return data


class JsonRpcRequest(BaseModel):
    """
    JSON-RPC 请求对象
    """
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[JsonRpcParams] = None
