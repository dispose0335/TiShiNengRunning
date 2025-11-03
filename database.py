"""
SQLAlchemy 异步数据库配置和会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os

# 数据库文件路径
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tsn_data.db")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 设置为 True 可以看到 SQL 语句日志
    poolclass=NullPool,  # SQLite 使用 NullPool
    future=True
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()


async def get_db():
    """
    获取数据库会话的异步生成器

    用法:
        async for db in get_db():
            # 使用 db 进行数据库操作
            pass

    或者在 FastAPI 中:
        async def some_endpoint(db: AsyncSession = Depends(get_db)):
            # 使用 db
            pass
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库,创建所有表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    关闭数据库连接
    """
    await engine.dispose()