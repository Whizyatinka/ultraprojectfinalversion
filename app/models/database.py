import asyncio
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import String, Integer, ForeignKey, DateTime, BigInteger, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import config


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    if config.USE_SQLITE:
        return "sqlite+aiosqlite:///telegram_bot.db"
    return f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"


async_engine = create_async_engine(
    get_database_url(),
    echo=False,
)

async_session_factory = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    stats: Mapped["UserStats"] = relationship("UserStats", back_populates="user", uselist=False)


class UserStats(Base):
    __tablename__ = "user_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), unique=True)
    manga_chapters_count: Mapped[int] = mapped_column(Integer, default=0)
    
    user: Mapped["User"] = relationship("User", back_populates="stats")


class CallbackData(Base):
    __tablename__ = "callback_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'chapter', 'volume', etc
    full_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DownloadedChapter(Base):
    __tablename__ = "downloaded_chapters"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    manga_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_number: Mapped[float] = mapped_column(nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # Уникальная комбинация: пользователь + манга + глава
        {'sqlite_autoincrement': True},
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await init_db()


if __name__ == "__main__":
    asyncio.run(main())
