from sqlalchemy.orm import Session as DbSession
from sqlalchemy import desc
from datetime import datetime
from typing import Optional, List, Tuple
import logging

from models.session import ApiKey, Session

logger = logging.getLogger(__name__)

class SessionService:
    """会话管理服务"""
    
    def __init__(self, db: DbSession):
        self.db = db
    
    def get_or_create_api_key(self, key: str) -> ApiKey:
        """
        获取或创建API密钥
        
        Args:
            key: API密钥字符串
            
        Returns:
            ApiKey对象
        """
        api_key = self.db.query(ApiKey).filter(ApiKey.key == key).first()
        
        if not api_key:
            logger.info(f"创建新的API密钥: {key}")
            api_key = ApiKey(key=key, last_used_at=datetime.utcnow())
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
        else:
            # 更新最后使用时间
            api_key.last_used_at = datetime.utcnow()
            self.db.commit()
            
        return api_key
    
    def create_session(self, api_key: str, session_id: str) -> Session:
        """
        创建新会话并关联到API密钥
        
        Args:
            api_key: API密钥字符串
            session_id: 会话ID
            
        Returns:
            新创建的Session对象
        """
        # 获取或创建API密钥
        api_key_obj = self.get_or_create_api_key(api_key)
        
        # 检查是否已存在相同session_id的会话
        existing_session = self.db.query(Session).filter(Session.session_id == session_id).first()
        if existing_session:
            logger.warning(f"会话ID已存在: {session_id}, 更新关联的API密钥")
            existing_session.api_key_id = api_key_obj.id
            existing_session.last_accessed = datetime.utcnow()
            self.db.commit()
            return existing_session
        
        # 检查此API密钥关联的会话数量
        session_count = self.db.query(Session).filter(Session.api_key_id == api_key_obj.id).count()
        
        # 如果会话数量超过限制，删除最旧的会话
        if session_count >= 5:
            oldest_session = (
                self.db.query(Session)
                .filter(Session.api_key_id == api_key_obj.id)
                .order_by(Session.last_accessed)
                .first()
            )
            if oldest_session:
                logger.info(f"API密钥 {api_key} 的会话数量超过限制，删除最旧的会话: {oldest_session.session_id}")
                self.db.delete(oldest_session)
                self.db.commit()
        
        # 创建新会话
        new_session = Session(
            session_id=session_id,
            api_key_id=api_key_obj.id
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return new_session
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """
        根据会话ID获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Session对象，如果不存在则返回None
        """
        return self.db.query(Session).filter(Session.session_id == session_id).first()
    
    def get_api_key_by_session_id(self, session_id: str) -> Optional[str]:
        """
        根据会话ID获取API密钥
        
        Args:
            session_id: 会话ID
            
        Returns:
            API密钥字符串，如果不存在则返回None
        """
        session = (
            self.db.query(Session)
            .filter(Session.session_id == session_id)
            .first()
        )
        
        if not session:
            return None
            
        api_key = self.db.query(ApiKey).filter(ApiKey.id == session.api_key_id).first()
        
        if not api_key:
            return None
            
        # 更新最后访问时间
        session.last_accessed = datetime.utcnow()
        api_key.last_used_at = datetime.utcnow()
        self.db.commit()
        
        return api_key.key
    
    def get_sessions_by_api_key(self, api_key: str) -> List[Session]:
        """
        根据API密钥获取关联的所有会话
        
        Args:
            api_key: API密钥字符串
            
        Returns:
            会话列表
        """
        api_key_obj = self.db.query(ApiKey).filter(ApiKey.key == api_key).first()
        
        if not api_key_obj:
            return []
            
        return (
            self.db.query(Session)
            .filter(Session.api_key_id == api_key_obj.id)
            .order_by(desc(Session.last_accessed))
            .all()
        )
        
    def update_session_access(self, session_id: str) -> bool:
        """
        更新会话的最后访问时间
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功更新
        """
        session = self.db.query(Session).filter(Session.session_id == session_id).first()
        
        if not session:
            return False
            
        session.last_accessed = datetime.utcnow()
        
        # 同时更新API密钥的最后使用时间
        api_key = self.db.query(ApiKey).filter(ApiKey.id == session.api_key_id).first()
        if api_key:
            api_key.last_used_at = datetime.utcnow()
            
        self.db.commit()
        return True
        
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功删除
        """
        session = self.db.query(Session).filter(Session.session_id == session_id).first()
        
        if not session:
            return False
            
        self.db.delete(session)
        self.db.commit()
        return True 