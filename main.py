from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow the Frontend to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, will change this to frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to NeuroLearn API"}

@app.get("/health")
def health_check():
    return {"status": "active", "service": "neurolearn-api"}