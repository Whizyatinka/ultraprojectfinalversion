import json
import hashlib
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.models.database import CallbackData


class CallbackManager:
    """Управление короткими callback_data для Telegram кнопок"""
    
    @staticmethod
    def _generate_short_id(user_id: int, data_type: str, full_data: str) -> str:
        """Генерирует короткий уникальный ID"""
        content = f"{user_id}:{data_type}:{full_data}:{datetime.utcnow().timestamp()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    @staticmethod
    async def create_callback(
        db: AsyncSession,
        user_id: int,
        data_type: str,
        data: dict
    ) -> str:
        """Создает короткий callback_data и сохраняет в БД"""
        full_data = json.dumps(data, ensure_ascii=False)
        short_id = CallbackManager._generate_short_id(user_id, data_type, full_data)
        
        # Проверяем, существует ли уже такой short_id
        result = await db.execute(
            select(CallbackData).where(CallbackData.short_id == short_id)
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            callback_data = CallbackData(
                short_id=short_id,
                user_id=user_id,
                data_type=data_type,
                full_data=full_data
            )
            db.add(callback_data)
            await db.commit()
        
        return short_id
    
    @staticmethod
    async def get_callback_data(
        db: AsyncSession,
        short_id: str,
        user_id: int
    ) -> Optional[dict]:
        """Получает полные данные по короткому ID"""
        result = await db.execute(
            select(CallbackData).where(
                CallbackData.short_id == short_id,
                CallbackData.user_id == user_id
            )
        )
        callback_data = result.scalar_one_or_none()
        
        if callback_data:
            return json.loads(callback_data.full_data)
        return None
    
    @staticmethod
    async def cleanup_old_callbacks(db: AsyncSession, days: int = 7):
        """Удаляет старые callback данные"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        await db.execute(
            delete(CallbackData).where(CallbackData.created_at < cutoff_date)
        )
        await db.commit()
