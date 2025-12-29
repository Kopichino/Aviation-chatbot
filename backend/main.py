import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# --- 1. SAFE ENV LOAD (For Local Testing) ---
# This allows the code to run on your laptop (loading .env) 
# AND on AWS (skipping .env) without crashing.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- 2. IMPORTS ---
# Import the AI Graph as 'bot_graph'
from backend.chatbot_graph import app as bot_graph 
# We only need get_all_leads for the admin panel now
from backend.dynamo_db import get_all_leads

# --- 3. INITIALIZE SERVER ---
api = FastAPI()

# --- 4. CORS MIDDLEWARE ---
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- 5. SETUP HANDLERS ---
handler = Mangum(api) 
templates = Jinja2Templates(directory="templates")

# --- 6. CHATBOT ROUTE ---
class UserInput(BaseModel):
    message: str
    session_id: str

@api.post("/chat")
async def chat_endpoint(user_input: UserInput):
    # We pass the user message to the graph
    state = {"messages": [("user", user_input.message)]}
    
    # thread_id is crucial! It helps the graph remember previous context/counts
    config = {"configurable": {"thread_id": user_input.session_id}}
    
    # Invoke the smart graph (It handles the limits, DB checks, and logic internally)
    result = bot_graph.invoke(state, config=config)
    
    # Extract the last message (Bot's reply)
    bot_reply = result["messages"][-1].content
    
    return {"response": bot_reply}

# --- 7. ADMIN & DATA ROUTES ---
@api.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@api.get("/api/leads")
async def get_leads_api():
    leads = get_all_leads()
    return {"leads": leads}