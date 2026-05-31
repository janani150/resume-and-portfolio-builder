# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, resume, portfolio, ai_agent

app = FastAPI(title="AI Resume Builder", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(portfolio.router)
app.include_router(ai_agent.router)   # ML Agent routes

@app.on_event("startup")
async def startup():
    print("AI Resume Builder API started!")
    print("ML Agent loaded and ready.")

@app.get("/")
def root():
    return {"message": "AI Resume Builder v2.0 — Now with custom ML!"}