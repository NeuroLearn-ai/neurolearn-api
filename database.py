from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. The Connection String
# Format: postgresql+asyncpg://user:password@service_name:port/db_name
# Note: "db" is the hostname because that is what we named the service in docker-compose
DATABASE_URL = "postgresql+asyncpg://neuro_admin:neuro_password@db:5432/neurolearn_db"

# 2. Create the Async Engine
engine = create_async_engine(DATABASE_URL, echo=True)   # echo=True for logging SQL queries

# 3. Create the Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False  # Prevents attributes from being expired after commit. Helps to avoid unnecessary re-queries.
)

# 4. The Base Class for our Models
Base = declarative_base()   # This maps to database tables

# 5. Dependency Injection
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()