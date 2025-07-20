import os
from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .ai.gemini import Gemini
from .auth.dependencies import get_user_identifier
from .auth.throttling import apply_rate_limit
from dotenv import load_dotenv
load_dotenv()

import os


# --- App Initialization ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
async def serve_index():
    return FileResponse("frontend/index.html")

# --- AI Configuration ---
def load_system_prompt():
    try:
        with open("src/prompts/system_prompt.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


system_prompt = load_system_prompt()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

ai_platform = Gemini(api_key=gemini_api_key, system_prompt=system_prompt)


# --- Pydantic Models ---
class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


# --- API Endpoints ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: str = Depends(get_user_identifier)):
    apply_rate_limit(user_id)
    response_text = ai_platform.chat(request.prompt)
    return ChatResponse(response=response_text)
