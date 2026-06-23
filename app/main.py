from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.routes import router
from app.api.jobs import router as jobs_router

load_dotenv()

app = FastAPI()

app.include_router(router)

app.include_router(jobs_router)