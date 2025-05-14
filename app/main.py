from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import notes

load_dotenv()

app = FastAPI(
    title=os.getenv("PROJECT_NAME", "Notes App API"),
    version=os.getenv("VERSION", "1.0.0"),
    openapi_url=f"{os.getenv('API_V1_STR', '/api/v1')}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix=f"{os.getenv('API_V1_STR', '/api/v1')}/auth", tags=["auth"]) 
app.include_router(notes.router, prefix=f"{os.getenv('API_V1_STR', '/api/v1')}/notes", tags=["notes"]) 