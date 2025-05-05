"""
API相关工具函数
"""

def mask_api_key(api_key: str) -> str:
    """
    对API密钥进行部分隐藏处理
    Args:
        api_key: 原始API密钥
    Returns:
        部分隐藏后的API密钥
    """
    if not api_key or len(api_key) < 8:
        return "***"
    
    # 保留前4位和后4位，中间用*替代
    visible_chars = 4
    return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars * 2) + api_key[-visible_chars:] 