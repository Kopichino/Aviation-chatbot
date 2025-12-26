from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import your Chatbot Logic
from backend.chatbot_graph import app 
# Import your Database Logic
from backend.mongo_db import get_all_leads
from mangum import Mangum

# Initialize App
api = FastAPI()

handler = Mangum(api) # Entry point for AWS Lambda

# Setup Templates (to serve HTML files)
templates = Jinja2Templates(directory="templates")

# --- 1. CHATBOT ROUTE (Existing) ---
class UserInput(BaseModel):
    message: str
    session_id: str

@api.post("/chat")
async def chat_endpoint(user_input: UserInput):
    state = {"messages": [("user", user_input.message)]}
    config = {"configurable": {"thread_id": user_input.session_id}}
    
    result = app.invoke(state, config=config)
    bot_reply = result["messages"][-1].content
    return {"response": bot_reply}

# --- 2. ADMIN PAGE ROUTE (New) ---
# This serves the visual HTML page
@api.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# --- 3. DATA API ROUTE (New) ---
# The HTML page will call this URL via JavaScript to get the data
@api.get("/api/leads")
async def get_leads_api():
    leads = get_all_leads()
    return {"leads": leads}