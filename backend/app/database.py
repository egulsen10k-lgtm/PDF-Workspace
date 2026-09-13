from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

def _make_engine(url: str):
    kwargs = {"echo": False}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_async_engine(url, **kwargs)

# Desktop pack defaults to SQLite next to the app. Postgres remains optional
# via DATABASE_URL and falls back automatically in init_db() if unreachable.
database_url = settings.FALLBACK_SQLITE_URL
engine = _make_engine(database_url)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    global engine, async_session_maker, database_url
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        if database_url != settings.FALLBACK_SQLITE_URL:
            logger.warning(f"Database {database_url} unavailable ({e}); falling back to SQLite.")
            await engine.dispose()
            database_url = settings.FALLBACK_SQLITE_URL
            engine = _make_engine(database_url)
            async_session_maker.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
