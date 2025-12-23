from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from backend.chatbot_graph import app  # Importing the brain

api = FastAPI(title="Aviation Chatbot API")

# Allow the frontend to talk to the backend
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

@api.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Prepare Input
        input_state = {
            "messages": [HumanMessage(content=request.message)]
        }
        
        # 2. Config
        config = {"configurable": {"thread_id": request.session_id}}
        
        # 3. Run Graph
        output = app.invoke(input_state, config=config)
        
        # 4. Get Response
        bot_response = output["messages"][-1].content
        
        return {"response": bot_response}

    except Exception as e:
        # --- ERROR HANDLING ---
        error_msg = str(e)
        
        # Check if it's the specific "Resource Exhausted" error
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "response": "⚠️ I am receiving too many requests right now! Please wait 10-15 seconds and try asking again."
            }
        
        # Other errors
        print(f"Server Error: {e}")
        return {
            "response": "⚠️ System Error. Please check the backend terminal."
        }
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="127.0.0.1", port=8000)