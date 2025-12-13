from fastapi import FastAPI
from app.routers import users, tweets, timeline
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Twitter-like System Design")

app.include_router(users.router)
app.include_router(tweets.router)
app.include_router(timeline.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Twitter-like API"}
