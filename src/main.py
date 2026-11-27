from fastapi import FastAPI

from src.routers import auth

app = FastAPI()
app.include_router(auth.router)
