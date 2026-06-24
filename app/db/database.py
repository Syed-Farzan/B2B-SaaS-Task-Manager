from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings

engine = create_async_engine(url=settings.DATABASE_URL)

session_local = async_sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with session_local() as session:
        yield session
