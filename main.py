from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from utils.db import Database
import uvicorn
from routers import user_route

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to Database.....")
    if Database.initialize():
        print("Connected to Database")
    else:
        print("Failed to connect to Database")
        raise RuntimeError("Database connection failed")
    yield
    print("Disconnecting from Database.....")
    Database._engine.dispose()
    print("Disconnected from Database")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
       "*"
    ],
    allow_credentials=True, 
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")