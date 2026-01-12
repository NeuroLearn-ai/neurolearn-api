from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
import asyncio
from database import engine, Base
import routers

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("🚀 Starting up... Waiting for Database...")
    
    # RETRY LOGIC: Try connecting 5 times with a 2-second delay
    for i in range(5):
        try:
            async with engine.begin() as conn:
                # This line triggers the actual connection check
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database Connected & Tables Created!")
            break # Success! Exit the loop
        except (OSError, OperationalError, ConnectionRefusedError) as e:
            print(f"⚠️ Database not ready yet (Attempt {i+1}/5)... waiting 2s")
            if i == 4: # Last attempt
                print("❌ Could not connect to DB after 5 attempts.")
                raise e
            await asyncio.sleep(2) # Non-blocking wait

    yield # App runs here
    
    # --- SHUTDOWN LOGIC ---
    print("🛑 Shutting down...")
    await engine.dispose()
    
app = FastAPI(lifespan=lifespan)

# Add Session Middleware (REQUIRED for Google Auth)
# This handles the temporary cookies needed during the login flow
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))

# Allow the Frontend to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to NeuroLearn API"}

@app.get("/health")
def health_check():
    return {"status": "active", "service": "neurolearn-api"}

app.include_router(routers.auth)
app.include_router(routers.notes)
app.include_router(routers.user)