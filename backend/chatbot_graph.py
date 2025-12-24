import os
import re
from typing import TypedDict, Annotated, List, Union, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# Imports for AI & DB
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from backend.database import save_lead  # <--- IMPORT OUR DB FUNCTION

load_dotenv()

# --- CONFIGURATION ---
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = PineconeVectorStore(
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings
)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    email: Union[str, None]
    phone: Union[str, None]
    query_count: int
    # Tracks where we are in the flow
    dialog_state: Literal["chatting", "asking_callback", "asking_phone"] 

# --- NODES ---

def router_node(state: AgentState):
    """Decides the next step based on state."""
    dialog_state = state.get("dialog_state", "chatting")
    
    # 1. Gate: Email Check
    if not state.get("email"):
        return "email_collection"

    # 2. Logic: Callback Offer Trigger (e.g., after 2 queries)
    # We check if we haven't asked yet (dialog_state is chatting) 
    # and we haven't got a phone number yet.
    if state.get("query_count", 0) >= 2 and dialog_state == "chatting" and not state.get("phone"):
        return "offer_callback"

    # 3. Handle Active Dialog States
    if dialog_state == "asking_callback":
        return "process_callback_response"
    
    if dialog_state == "asking_phone":
        return "process_phone_input"

    # 4. Default: RAG Chat
    return "rag_chat"

def email_collection_node(state: AgentState):
    messages = state["messages"]
    last_user_msg = messages[-1].content
    email_pattern = r"[^@]+@[^@]+\.[^@]+"
    
    if len(messages) <= 1:
        return {"messages": [AIMessage(content="Welcome to MH Cockpit! To assist you with brochures and fees, please share your **email address**.")]}

    if re.search(email_pattern, last_user_msg):
        return {
            "email": last_user_msg,
            "messages": [AIMessage(content="Thank you! How can I help you with your pilot training today?")],
            "query_count": 0,
            "dialog_state": "chatting"
        }
    return {"messages": [AIMessage(content="That looks invalid. Please enter a valid email address.")]}

def rag_chat_node(state: AgentState):
    messages = state["messages"]
    user_query = messages[-1].content
    
    # RAG Search
    docs = vector_store.similarity_search(user_query, k=5)
    context_text = "\n\n".join([d.page_content for d in docs])
    
    system_prompt = (
        "ROLE & TONE:\n"
        "You are the official voice of **MH Cockpit Aviation Academy**. "
        "Speak directly as 'We' (the academy). "
        "**CRITICAL RULE:** NEVER explicitly state your title, role, or that you are an AI (e.g., DO NOT say 'As the Senior Ambassador' or 'As an expert'). Just answer the question directly and confidently.\n\n"

        "INSTRUCTIONS:\n"
        "1. **Context is King:** Your highest priority is to use the specific facts, lists, and data provided in the CONTEXT below. If the context contains a list of recruiters (e.g., Air India, Indigo, etc.), you MUST explicitly list them. Do not summarize or say 'various airlines'—name them.\n"
        "2. **Brand Advocacy:** You are biased towards MH Cockpit. Describe our courses as 'industry-leading' and our partner universities (like VELS) as 'excellent' or 'top-tier' choices.\n"
        "3. **Scope:** Answer only aviation and academy-related queries. Polite refusal for other topics.\n"
        "4. **Direct Answers:** If the user asks for recruiters, give the list immediately. Do not preach about 'market demand' or 'hiring cycles' unless the context specifically says so.\n\n"
        
        f"CONTEXT DATA:\n{context_text}"
    )
    # print("--- WHAT THE BOT SEES ---")
    # print(context_text) 
    # print("-------------------------")
    response = llm.invoke([SystemMessage(content=system_prompt)] + messages[-5:])
    
    return {
        "messages": [response],
        "query_count": state.get("query_count", 0) + 1
    }

# --- NEW NODES FOR LEAD GEN ---

def offer_callback_node(state: AgentState):
    """Asks user if they want a call."""
    msg = "I hope I am answering your questions well! Would you like a **callback from our senior captain** to discuss customized career paths? (Yes/No)"
    return {
        "messages": [AIMessage(content=msg)],
        "dialog_state": "asking_callback"
    }

def process_callback_response_node(state: AgentState):
    """Analyzes if user said Yes or No."""
    last_msg = state["messages"][-1].content.lower()
    
    if "yes" in last_msg or "sure" in last_msg or "ok" in last_msg:
        return {
            "messages": [AIMessage(content="Great! Please share your **Phone Number** so we can reach you.")],
            "dialog_state": "asking_phone"
        }
    else:
        # User said No
        return {
            "messages": [AIMessage(content="No problem! Let's continue chatting. What else would you like to know?")],
            "dialog_state": "chatting",
            "phone": "skipped" # Mark skipped so we don't ask again
        }

def process_phone_input_node(state: AgentState):
    """Validates phone and saves to DB."""
    phone_input = state["messages"][-1].content
    # Basic validation (checking for digits)
    if any(char.isdigit() for char in phone_input):
        # --- SAVE TO DATABASE ---
        email = state.get("email")
        save_lead(email, phone_input)
        
        return {
            "messages": [AIMessage(content="Perfect. We have saved your details and will call you shortly! What other questions do you have?")],
            "dialog_state": "chatting",
            "phone": phone_input
        }
    else:
        return {
            "messages": [AIMessage(content="That doesn't look like a valid number. Please enter digits only.")],
            "dialog_state": "asking_phone" # Stay in this state
        }

# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("email_collection", email_collection_node)
workflow.add_node("rag_chat", rag_chat_node)
workflow.add_node("offer_callback", offer_callback_node)
workflow.add_node("process_callback_response", process_callback_response_node)
workflow.add_node("process_phone_input", process_phone_input_node)

# Set Logic
workflow.set_conditional_entry_point(
    router_node,
    {
        "email_collection": "email_collection",
        "rag_chat": "rag_chat",
        "offer_callback": "offer_callback",
        "process_callback_response": "process_callback_response",
        "process_phone_input": "process_phone_input"
    }
)

# All nodes loop back to END to wait for next user input
workflow.add_edge("email_collection", END)
workflow.add_edge("rag_chat", END)
workflow.add_edge("offer_callback", END)
workflow.add_edge("process_callback_response", END)
workflow.add_edge("process_phone_input", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)