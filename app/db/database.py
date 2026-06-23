from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

URL = "postgresql+asyncpg://postgres:12345@db:5432/saas_task_manager"

engine = create_async_engine(url=URL)

session_local = async_sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with session_local() as session:
        yield session
