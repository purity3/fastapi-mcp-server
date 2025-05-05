import httpx
from config import API_URL, API_KEY_PREFIX
from urllib.parse import urljoin

async def verify_api_key(api_key: str) -> bool:
    """
    验证API密钥是否有效
    
    Args:
        api_key: 要验证的API密钥
    
    Returns:
        如果API密钥有效则返回True，否则返回False
    """
    # 验证API密钥前缀
    if not api_key.startswith(API_KEY_PREFIX):
        print(f"API密钥前缀无效: {api_key}")
        return False
        
    try:
        # 使用urljoin构建URL，自动处理尾部斜杠问题
        verify_url = urljoin(API_URL, "api/tools/verify")
        
        async with httpx.AsyncClient() as client:
            headers = {"x-api-key": api_key}
            response = await client.get(verify_url, headers=headers)
            data = response.json()
            
            if response.status_code == 200 and data.get("data", {}).get("valid", False):
                return True
            return False
    except Exception as e:
        print(f"API密钥验证失败: {e}")
        return False
