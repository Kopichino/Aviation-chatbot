from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# --- 1. RENAME IMPORT TO AVOID CONFLICT ---
# Import the AI Graph as 'bot_graph' instead of 'app'
from backend.chatbot_graph import app as bot_graph 

from backend.dynamo_db import save_lead_dynamo, get_all_leads

# --- 2. INITIALIZE SERVER AS 'api' ---
api = FastAPI()

# --- 3. ADD MIDDLEWARE TO 'api' (Not bot_graph) ---
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

handler = Mangum(api) 
templates = Jinja2Templates(directory="templates")

# --- 4. CHATBOT ROUTE ---
class UserInput(BaseModel):
    message: str
    session_id: str

@api.post("/chat")
async def chat_endpoint(user_input: UserInput):
    state = {"messages": [("user", user_input.message)]}
    config = {"configurable": {"thread_id": user_input.session_id}}
    
    # Use the renamed 'bot_graph' here
    result = bot_graph.invoke(state, config=config)
    
    bot_reply = result["messages"][-1].content
    return {"response": bot_reply}

# --- 5. ADMIN & DATA ROUTES ---
@api.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@api.get("/api/leads")
async def get_leads_api():
    leads = get_all_leads()
    return {"leads": leads}