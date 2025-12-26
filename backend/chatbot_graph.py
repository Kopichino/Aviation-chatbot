import os
import re
from datetime import datetime
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
# from backend.database import save_lead 
from backend.mongo_db import save_lead_mongo

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

# --- HELPER FUNCTION (CRASH FIX) ---
def get_safe_content(message: Union[BaseMessage, str]) -> str:
    """Safely extracts string content from a message, handling Lists/Dicts."""
    # If it's already just a string, return it
    if isinstance(message, str):
        return message
    
    # If it's a LangChain Message object, get .content
    content = message.content
    
    # If content is a list (Gemini often returns this), join it into one string
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        return " ".join(text_parts)
    
    return str(content)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    email: Union[str, None]
    phone: Union[str, None]
    name: Union[str, None]
    school: Union[str, None] 
    city: Union[str, None]   
    query_count: int
    pending_query: Union[str, None] # Stores the question asked BEFORE interruption
    dialog_state: Literal["chatting", "asking_phone", "asking_school", "limit_reached"] 

# --- NODES ---

def router_node(state: AgentState):
    """Decides the next step based on state."""
    dialog_state = state.get("dialog_state", "chatting")
    query_count = state.get("query_count", 0)
    
    # 0. Block if Limit Reached
    if dialog_state == "limit_reached":
        return "limit_exhausted"

    # 1. Gate: Email Check
    if not state.get("email"):
        return "email_collection"

    # 2. Handle Active Input States
    if dialog_state == "asking_school":
        return "process_school_input"

    if dialog_state == "asking_phone":
        return "process_phone_input"

    # --- FLOW LOGIC ---
    # 3. Ask School & City (After 3 queries)
    if query_count >= 3 and not state.get("school"):
        return "ask_school_city"

    # 4. Ask Phone Number (After 6 queries)
    if query_count >= 6 and not state.get("phone"):
        return "ask_phone"

    # 5. Limit Exhausted (After 9 queries)
    if query_count >= 9:
        return "limit_exhausted"

    # 6. Default: RAG Chat
    return "rag_chat"

# --- NODE FUNCTIONS ---

def email_collection_node(state: AgentState):
    messages = state["messages"]
    last_user_msg = messages[-1].content.strip()
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

def ask_school_city_node(state: AgentState):
    # Capture the question the user JUST asked
    last_msg = get_safe_content(state["messages"][-1])
    
    return {
        "messages": [AIMessage(content="I'd love to answer that! But first, could you quickly tell me your **Name**, **School**, and **City**? (Format: Name, School, City)")],
        "dialog_state": "asking_school",
        "pending_query": last_msg 
    }

def process_school_input_node(state: AgentState):
    user_input = get_safe_content(state["messages"][-1])
    
    # Default values
    name, school, city = "Not specified", "Not specified", "Not specified"

    # Split by comma (Expects: Name, School, City)
    if "," in user_input:
        parts = [p.strip() for p in user_input.split(",")]
        if len(parts) >= 3:
            name, school, city = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            name, school = parts[0], parts[1]
    else:
        # If user just types one thing, assume it's the name
        name = user_input.strip()

    prev_q = state.get("pending_query", "your previous question")
    
    # --- SAVE TO MONGO IMMEDIATELY ---
    email = state.get("email")
    if email:
        try:
            # We save partial details now. Phone comes later.
            save_lead_mongo(email, name=name, school=school, city=city)
            print(f"✅ Personal Details Saved: {name}, {school}, {city}")
        except Exception as e:
            print(f"⚠️ Mongo Save Warning: {e}")
    # ---------------------------------

    return {
        "messages": [AIMessage(content=f"Nice to meet you, {name}! I've updated your profile. Now, regarding **'{prev_q}'**... could you please ask that again?")],
        "dialog_state": "chatting",
        "name": name,   # Add this to AgentState definition if missing!
        "school": school, 
        "city": city
    }

def ask_phone_node(state: AgentState):
    return {
        "messages": [AIMessage(content="To provide you with better assistance and brochure details, could you please share your **Phone Number**?")],
        "dialog_state": "asking_phone"
    }

def process_phone_input_node(state: AgentState):
    # 1. Get content safely
    phone_input = get_safe_content(state["messages"][-1])
    
    # 2. CLEAN: Extract only digits
    digits_only = "".join(filter(str.isdigit, phone_input))
    
    # 3. VALIDATE
    if 10 <= len(digits_only) <= 15:
        email = state.get("email")
        
        if email:
            # --- PREPARE CHAT HISTORY ---
            # Convert complex LangChain objects to simple JSON for MongoDB
            history_log = []
            for msg in state["messages"]:
                role = "user" if isinstance(msg, HumanMessage) else "bot"
                # Handle content safely
                content = get_safe_content(msg)
                history_log.append({"role": role, "content": content, "timestamp": str(datetime.now())})

            # --- SAVE TO MONGO ---
            try:
                save_lead_mongo(email, phone=digits_only, chat_history=history_log)
                print(f"✅ Lead & History Secured: {email}")
            except Exception as e:
                print(f"⚠️ Mongo Save Warning: {e}")
            # ---------------------

        return {
            "messages": [AIMessage(content="Thanks! I've noted that. You can ask me **2 more questions** before we wrap up.")],
            "dialog_state": "chatting",
            "phone": digits_only
        }
    else:
        return {
            "messages": [AIMessage(content="That doesn't look like a valid number. Please enter a valid **10-digit mobile number**.")],
            "dialog_state": "asking_phone"
        }

def limit_exhausted_node(state: AgentState):
    email = state.get("email")
    name = state.get("name")
    phone = state.get("phone")
    school = state.get("school")
    city = state.get("city")
    
    # Save to DB (Safe Call)
    if email and phone:
        try:
            # Ensure your database.py accepts 4 arguments!
            save_lead_mongo(email, phone, school, city)
            print(f"✅ Lead Saved: {email}")
        except Exception as e:
            print(f"❌ DATABASE ERROR: {e}") 
    
    msg = "Thank you for your interest! **Your query limit has been exhausted.** For further details and a personalized counseling session, please contact our office directly."
    
    return {
        "messages": [AIMessage(content=msg)],
        "dialog_state": "limit_reached" 
    }

def rag_chat_node(state: AgentState):
    """RAG Chat with CRASH PROTECTION & Safe Content Handling."""
    try:
        messages = state["messages"]
        user_query = messages[-1].content
        
        # --- SMART CONTEXT RESTORATION ---
        pending_q = state.get("pending_query")
        
        # If user says "what?" or "answer me" after an interruption, swap it with the saved question
        if pending_q and (len(user_query.split()) < 5 or "previous" in user_query.lower() or "answer" in user_query.lower() or "what" in user_query.lower()):
            print(f"🔄 Swapping '{user_query}' with pending query: '{pending_q}'")
            search_query = pending_q
            # We updated the search query, but we keep the pending_q in state just in case
        else:
            search_query = user_query
            # If they asked a BRAND NEW specific question (long text), clear the pending one
            if pending_q and len(user_query.split()) > 5:
                state["pending_query"] = None

        # 1. Search Vector DB
        docs = vector_store.similarity_search(search_query, k=5)
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. Filter History (CRASH FIX IS HERE)
        clean_history = []
        for msg in messages[-6:]:
            # --- FIX: Safely convert content to string ---
            raw_content = msg.content
            if isinstance(raw_content, list):
                # Join all parts if it's a list
                text_parts = []
                for part in raw_content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                content_str = " ".join(text_parts)
            else:
                content_str = str(raw_content)
            # ---------------------------------------------

            # Now safely check .lower()
            if "which school" in content_str.lower() or "updated your profile" in content_str.lower() or "format: school" in content_str.lower():
                continue # Skip the interruption messages
            
            clean_history.append(msg)

        system_prompt = (
            "ROLE & TONE:\n"
            "You are the official voice of **MH Cockpit Aviation Academy**. "
            "Speak directly as 'We' (the academy). "
            "**CRITICAL RULE:** NEVER explicitly state your title, role, or that you are an AI (e.g., DO NOT say 'As the Senior Ambassador' or 'As an expert'). Just answer the question directly and confidently.\n\n"

            "INSTRUCTIONS:\n"
            "1. **Context is King:** Your highest priority is to use the specific facts, lists, and data provided in the CONTEXT below. If the context contains a list of recruiters (e.g., Air India, Indigo, etc.), you MUST explicitly list them. Do not summarize or say 'various airlines'—name them.\n"
            "2. **Brand Advocacy:** You are biased towards MH Cockpit. Describe our courses as 'industry-leading' and our partner universities (like VELS) as 'excellent' or 'top-tier' choices.\n"
            "3. **Scope:** Answer only aviation and academy-related queries. Polite refusal for other topics.\n"
            "4. **Direct Answers:** If the user asks for recruiters, give the list immediately. Do not preach about 'market demand' or 'hiring cycles' unless the context specifically says so.\n"
            "5. **Contextual Answers:** If asked about any eligibility criteria review the attached document properly and answer in context with it. Do not hallucinate or mislead with wrong information. \n"
            
            f"CONTEXT DATA:\n{context_text}"
        )
        
        response = llm.invoke([SystemMessage(content=system_prompt)] + clean_history)
        
        return {
            "messages": [response],
            "query_count": state.get("query_count", 0) + 1,
            "pending_query": None # Clear it after answering
        }
        
    except Exception as e:
        print(f"❌ AI ERROR: {e}")
        # Return a polite error message instead of crashing
        return {
            "messages": [AIMessage(content="I apologize, but I'm having trouble accessing that info right now. Could you please rephrase your question?")],
            "query_count": state.get("query_count", 0) 
        }
    
# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("email_collection", email_collection_node)
workflow.add_node("rag_chat", rag_chat_node)
workflow.add_node("ask_phone", ask_phone_node)
workflow.add_node("process_phone_input", process_phone_input_node)
workflow.add_node("ask_school_city", ask_school_city_node)
workflow.add_node("process_school_input", process_school_input_node)
workflow.add_node("limit_exhausted", limit_exhausted_node)

# Set Logic
workflow.set_conditional_entry_point(
    router_node,
    {
        "email_collection": "email_collection",
        "rag_chat": "rag_chat",
        "ask_phone": "ask_phone",
        "process_phone_input": "process_phone_input",
        "ask_school_city": "ask_school_city",
        "process_school_input": "process_school_input",
        "limit_exhausted": "limit_exhausted"
    }
)

# Edges
workflow.add_edge("email_collection", END)
workflow.add_edge("rag_chat", END)
workflow.add_edge("ask_phone", END)
workflow.add_edge("process_phone_input", END)
workflow.add_edge("ask_school_city", END)
workflow.add_edge("process_school_input", END)
workflow.add_edge("limit_exhausted", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)