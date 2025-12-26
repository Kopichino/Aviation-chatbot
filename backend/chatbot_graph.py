# import os
# import re
# from typing import TypedDict, Annotated, List, Union, Literal
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph.message import add_messages

# # Imports for AI & DB
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from dotenv import load_dotenv
# from backend.database import save_lead  # <--- IMPORT OUR DB FUNCTION

# load_dotenv()

# # --- CONFIGURATION ---
# PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# llm = ChatGoogleGenerativeAI(
#     model="gemini-flash-latest",
#     temperature=0,
#     google_api_key=GOOGLE_API_KEY
# )

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# vector_store = PineconeVectorStore(
#     index_name=PINECONE_INDEX_NAME,
#     embedding=embeddings
# )

# # --- STATE DEFINITION ---
# class AgentState(TypedDict):
#     messages: Annotated[List[BaseMessage], add_messages]
#     email: Union[str, None]
#     phone: Union[str, None]
#     query_count: int
#     # Tracks where we are in the flow
#     dialog_state: Literal["chatting", "asking_callback", "asking_phone"] 

# # --- NODES ---

# def router_node(state: AgentState):
#     """Decides the next step based on state."""
#     dialog_state = state.get("dialog_state", "chatting")
    
#     # 1. Gate: Email Check
#     if not state.get("email"):
#         return "email_collection"

#     # 2. Logic: Callback Offer Trigger (e.g., after 2 queries)
#     # We check if we haven't asked yet (dialog_state is chatting) 
#     # and we haven't got a phone number yet.
#     if state.get("query_count", 0) >= 2 and dialog_state == "chatting" and not state.get("phone"):
#         return "offer_callback"

#     # 3. Handle Active Dialog States
#     if dialog_state == "asking_callback":
#         return "process_callback_response"
    
#     if dialog_state == "asking_phone":
#         return "process_phone_input"

#     # 4. Default: RAG Chat
#     return "rag_chat"

# def email_collection_node(state: AgentState):
#     messages = state["messages"]
#     last_user_msg = messages[-1].content
#     email_pattern = r"[^@]+@[^@]+\.[^@]+"
    
#     if len(messages) <= 1:
#         return {"messages": [AIMessage(content="Welcome to MH Cockpit! To assist you with brochures and fees, please share your **email address**.")]}

#     if re.search(email_pattern, last_user_msg):
#         return {
#             "email": last_user_msg,
#             "messages": [AIMessage(content="Thank you! How can I help you with your pilot training today?")],
#             "query_count": 0,
#             "dialog_state": "chatting"
#         }
#     return {"messages": [AIMessage(content="That looks invalid. Please enter a valid email address.")]}

# def rag_chat_node(state: AgentState):
#     messages = state["messages"]
#     user_query = messages[-1].content
    
#     # RAG Search
#     docs = vector_store.similarity_search(user_query, k=5)
#     context_text = "\n\n".join([d.page_content for d in docs])
    
#     system_prompt = (
#         "ROLE & TONE:\n"
#         "You are the official voice of **MH Cockpit Aviation Academy**. "
#         "Speak directly as 'We' (the academy). "
#         "**CRITICAL RULE:** NEVER explicitly state your title, role, or that you are an AI (e.g., DO NOT say 'As the Senior Ambassador' or 'As an expert'). Just answer the question directly and confidently.\n\n"

#         "INSTRUCTIONS:\n"
#         "1. **Context is King:** Your highest priority is to use the specific facts, lists, and data provided in the CONTEXT below. If the context contains a list of recruiters (e.g., Air India, Indigo, etc.), you MUST explicitly list them. Do not summarize or say 'various airlines'—name them.\n"
#         "2. **Brand Advocacy:** You are biased towards MH Cockpit. Describe our courses as 'industry-leading' and our partner universities (like VELS) as 'excellent' or 'top-tier' choices.\n"
#         "3. **Scope:** Answer only aviation and academy-related queries. Polite refusal for other topics.\n"
#         "4. **Direct Answers:** If the user asks for recruiters, give the list immediately. Do not preach about 'market demand' or 'hiring cycles' unless the context specifically says so.\n\n"
        
#         f"CONTEXT DATA:\n{context_text}"
#     )
#     # print("--- WHAT THE BOT SEES ---")
#     # print(context_text) 
#     # print("-------------------------")
#     response = llm.invoke([SystemMessage(content=system_prompt)] + messages[-5:])
    
#     return {
#         "messages": [response],
#         "query_count": state.get("query_count", 0) + 1
#     }

# # --- NEW NODES FOR LEAD GEN ---

# def offer_callback_node(state: AgentState):
#     """Asks user if they want a call."""
#     msg = "I hope I am answering your questions well! Would you like a **callback from our senior captain** to discuss customized career paths? (Yes/No)"
#     return {
#         "messages": [AIMessage(content=msg)],
#         "dialog_state": "asking_callback"
#     }

# def process_callback_response_node(state: AgentState):
#     """Analyzes if user said Yes or No."""
#     last_msg = state["messages"][-1].content.lower()
    
#     if "yes" in last_msg or "sure" in last_msg or "ok" in last_msg:
#         return {
#             "messages": [AIMessage(content="Great! Please share your **Phone Number** so we can reach you.")],
#             "dialog_state": "asking_phone"
#         }
#     else:
#         # User said No
#         return {
#             "messages": [AIMessage(content="No problem! Let's continue chatting. What else would you like to know?")],
#             "dialog_state": "chatting",
#             "phone": "skipped" # Mark skipped so we don't ask again
#         }

# def process_phone_input_node(state: AgentState):
#     """Validates phone and saves to DB."""
#     phone_input = state["messages"][-1].content
#     # Basic validation (checking for digits)
#     if any(char.isdigit() for char in phone_input):
#         # --- SAVE TO DATABASE ---
#         email = state.get("email")
#         save_lead(email, phone_input)
        
#         return {
#             "messages": [AIMessage(content="Perfect. We have saved your details and will call you shortly! What other questions do you have?")],
#             "dialog_state": "chatting",
#             "phone": phone_input
#         }
#     else:
#         return {
#             "messages": [AIMessage(content="That doesn't look like a valid number. Please enter digits only.")],
#             "dialog_state": "asking_phone" # Stay in this state
#         }

# # --- BUILD GRAPH ---
# workflow = StateGraph(AgentState)

# # Add Nodes
# workflow.add_node("email_collection", email_collection_node)
# workflow.add_node("rag_chat", rag_chat_node)
# workflow.add_node("offer_callback", offer_callback_node)
# workflow.add_node("process_callback_response", process_callback_response_node)
# workflow.add_node("process_phone_input", process_phone_input_node)

# # Set Logic
# workflow.set_conditional_entry_point(
#     router_node,
#     {
#         "email_collection": "email_collection",
#         "rag_chat": "rag_chat",
#         "offer_callback": "offer_callback",
#         "process_callback_response": "process_callback_response",
#         "process_phone_input": "process_phone_input"
#     }
# )

# # All nodes loop back to END to wait for next user input
# workflow.add_edge("email_collection", END)
# workflow.add_edge("rag_chat", END)
# workflow.add_edge("offer_callback", END)
# workflow.add_edge("process_callback_response", END)
# workflow.add_edge("process_phone_input", END)

# memory = MemorySaver()
# app = workflow.compile(checkpointer=memory)

# import os
# import re
# from typing import TypedDict, Annotated, List, Union, Literal
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph.message import add_messages

# # Imports for AI & DB
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from dotenv import load_dotenv
# from backend.database import save_lead 

# load_dotenv()

# # --- CONFIGURATION ---
# PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# llm = ChatGoogleGenerativeAI(
#     model="gemini-flash-latest",
#     temperature=0,
#     google_api_key=GOOGLE_API_KEY
# )

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# vector_store = PineconeVectorStore(
#     index_name=PINECONE_INDEX_NAME,
#     embedding=embeddings
# )

# # --- STATE DEFINITION ---
# class AgentState(TypedDict):
#     messages: Annotated[List[BaseMessage], add_messages]
#     email: Union[str, None]
#     phone: Union[str, None]
#     school: Union[str, None] # Added
#     city: Union[str, None]   # Added
#     query_count: int
#     # Tracks where we are in the flow
#     dialog_state: Literal["chatting", "asking_phone", "asking_school", "limit_reached"] 

# # --- NODES ---

# def router_node(state: AgentState):
#     """Decides the next step based on state."""
#     dialog_state = state.get("dialog_state", "chatting")
#     query_count = state.get("query_count", 0)
    
#     # 0. Block if Limit Reached
#     if dialog_state == "limit_reached":
#         return "limit_exhausted"

#     # 1. Gate: Email Check (Priority 1)
#     if not state.get("email"):
#         return "email_collection"

#     # 2. Handle Active Input States (User just replied to a specific question)
#     if dialog_state == "asking_phone":
#         return "process_phone_input"
    
#     if dialog_state == "asking_school":
#         return "process_school_input"

#     # 3. Logic: Force Phone Number (After 2 queries)
#     if query_count >= 2 and not state.get("phone"):
#         return "ask_phone"

#     # 4. Logic: Force School/City (After 3 MORE queries => Total 5)
#     if query_count >= 5 and not state.get("school"):
#         return "ask_school_city"

#     # 5. Logic: Limit Exhausted (After 2 MORE queries => Total 7)
#     if query_count >= 7:
#         return "limit_exhausted"

#     # 6. Default: RAG Chat
#     return "rag_chat"

# # --- NODE FUNCTIONS ---

# def email_collection_node(state: AgentState):
#     messages = state["messages"]
#     last_user_msg = messages[-1].content
#     email_pattern = r"[^@]+@[^@]+\.[^@]+"
    
#     # First interaction
#     if len(messages) <= 1:
#         return {"messages": [AIMessage(content="Welcome to MH Cockpit! To assist you with brochures and fees, please share your **email address**.")]}

#     # Validate Email
#     if re.search(email_pattern, last_user_msg):
#         return {
#             "email": last_user_msg,
#             "messages": [AIMessage(content="Thank you! How can I help you with your pilot training today?")],
#             "query_count": 0,
#             "dialog_state": "chatting"
#         }
#     return {"messages": [AIMessage(content="That looks invalid. Please enter a valid email address.")]}

# def ask_phone_node(state: AgentState):
#     """Interrupts chat to ask for phone number directly."""
#     return {
#         "messages": [AIMessage(content="To provide you with better assistance and brochure details, could you please share your **Phone Number**?")],
#         "dialog_state": "asking_phone"
#     }

# def process_phone_input_node(state: AgentState):
#     """Validates phone and saves to DB."""
#     phone_input = state["messages"][-1].content
    
#     # Basic validation (digits check)
#     if any(char.isdigit() for char in phone_input):
#         email = state.get("email")
        
#         # Save to DB
#         save_lead(email, phone_input) 
        
#         return {
#             "messages": [AIMessage(content="Thanks! I've noted that. What else would you like to know?")],
#             "dialog_state": "chatting",
#             "phone": phone_input
#         }
#     else:
#         return {
#             "messages": [AIMessage(content="That doesn't look like a valid number. Please enter digits only.")],
#             "dialog_state": "asking_phone" # Stay in this state
#         }

# def ask_school_city_node(state: AgentState):
#     """Interrupts chat to ask for School and City."""
#     return {
#         "messages": [AIMessage(content="Just a quick question for our records: **Which School are you studying in, and in which City?**")],
#         "dialog_state": "asking_school"
#     }

# def process_school_input_node(state: AgentState):
#     """Captures school and city info."""
#     user_input = state["messages"][-1].content
    
#     # Here we just save the raw text as school info for simplicity
#     # You could add another DB call here to update the user record if needed
    
#     return {
#         "messages": [AIMessage(content="Great, thank you! Let's continue. What is your next question?")],
#         "dialog_state": "chatting",
#         "school": user_input, # Marking as done
#         "city": "captured"    # Marking as done
#     }

# def limit_exhausted_node(state: AgentState):
#     """Final state when queries are exhausted."""
#     msg = "Thank you for your interest! **Your query limit has been exhausted.** For further details and a personalized counseling session, please contact our office directly."
    
#     return {
#         "messages": [AIMessage(content=msg)],
#         "dialog_state": "limit_reached" # Locks the state
#     }

# def rag_chat_node(state: AgentState):
#     messages = state["messages"]
#     user_query = messages[-1].content
    
#     # RAG Search
#     docs = vector_store.similarity_search(user_query, k=5)
#     context_text = "\n\n".join([d.page_content for d in docs])
    
#     system_prompt = (
#         "ROLE & TONE:\n"
#         "You are the official voice of **MH Cockpit Aviation Academy**. "
#         "Speak directly as 'We' (the academy). "
#         "**CRITICAL RULE:** NEVER explicitly state your title, role, or that you are an AI (e.g., DO NOT say 'As the Senior Ambassador' or 'As an expert'). Just answer the question directly and confidently.\n\n"

#         "INSTRUCTIONS:\n"
#         "1. **Context is King:** Your highest priority is to use the specific facts, lists, and data provided in the CONTEXT below. If the context contains a list of recruiters (e.g., Air India, Indigo, etc.), you MUST explicitly list them. Do not summarize or say 'various airlines'—name them.\n"
#         "2. **Brand Advocacy:** You are biased towards MH Cockpit. Describe our courses as 'industry-leading' and our partner universities (like VELS) as 'excellent' or 'top-tier' choices.\n"
#         "3. **Scope:** Answer only aviation and academy-related queries. Polite refusal for other topics.\n"
#         "4. **Direct Answers:** If the user asks for recruiters, give the list immediately. Do not preach about 'market demand' or 'hiring cycles' unless the context specifically says so.\n\n"
        
#         f"CONTEXT DATA:\n{context_text}"
#     )
    
#     response = llm.invoke([SystemMessage(content=system_prompt)] + messages[-5:])
    
#     return {
#         "messages": [response],
#         "query_count": state.get("query_count", 0) + 1
#     }

# # --- BUILD GRAPH ---
# workflow = StateGraph(AgentState)

# # Add Nodes
# workflow.add_node("email_collection", email_collection_node)
# workflow.add_node("rag_chat", rag_chat_node)
# workflow.add_node("ask_phone", ask_phone_node)
# workflow.add_node("process_phone_input", process_phone_input_node)
# workflow.add_node("ask_school_city", ask_school_city_node)
# workflow.add_node("process_school_input", process_school_input_node)
# workflow.add_node("limit_exhausted", limit_exhausted_node)

# # Set Logic
# workflow.set_conditional_entry_point(
#     router_node,
#     {
#         "email_collection": "email_collection",
#         "rag_chat": "rag_chat",
#         "ask_phone": "ask_phone",
#         "process_phone_input": "process_phone_input",
#         "ask_school_city": "ask_school_city",
#         "process_school_input": "process_school_input",
#         "limit_exhausted": "limit_exhausted"
#     }
# )

# # Edges
# workflow.add_edge("email_collection", END)
# workflow.add_edge("rag_chat", END)
# workflow.add_edge("ask_phone", END)
# workflow.add_edge("process_phone_input", END)
# workflow.add_edge("ask_school_city", END)
# workflow.add_edge("process_school_input", END)
# workflow.add_edge("limit_exhausted", END)

# memory = MemorySaver()
# app = workflow.compile(checkpointer=memory)

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
from backend.database import save_lead 

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
    # Capture the question the user JUST asked so we don't lose it
    last_message = state["messages"][-1]
    last_question = last_message.content if isinstance(last_message, HumanMessage) else "your question"
    
    return {
        "messages": [AIMessage(content="I'd love to answer that! But first, could you quickly tell me **which School you are studying in** and your **City**? (Format: School, City)")],
        "dialog_state": "asking_school",
        "pending_query": last_question # <--- SAVE IT
    }

def process_school_input_node(state: AgentState):
    user_input = state["messages"][-1].content
    
    if "," in user_input:
        parts = user_input.split(",", 1)
        school = parts[0].strip()
        city = parts[1].strip()
    else:
        school = user_input.strip()
        city = "Not specified"

    # Retrieve the saved question
    prev_q = state.get("pending_query", "your previous question")

    return {
        "messages": [AIMessage(content=f"Thanks! I've updated your profile. Now, you were asking: **'{prev_q}'**. \n\nCan you ask the question again please?")],
        "dialog_state": "chatting",
        "school": school, 
        "city": city,
        # We DO NOT clear pending_query yet, so RAG node can use it
    }

def ask_phone_node(state: AgentState):
    return {
        "messages": [AIMessage(content="To provide you with better assistance and brochure details, could you please share your **Phone Number**?")],
        "dialog_state": "asking_phone"
    }

def process_phone_input_node(state: AgentState):
    # 1. Get content safely
    phone_input = get_safe_content(state["messages"][-1])
    
    # 2. CLEAN: Extract only the digits from the input
    # e.g., "My number is +91-98765 43210" -> "919876543210"
    digits_only = "".join(filter(str.isdigit, phone_input))
    
    # 3. VALIDATE: Check if digit count is reasonable (10 to 15 digits)
    if 10 <= len(digits_only) <= 15:
        
        # --- SAVE IMMEDIATELY ---
        email = state.get("email")
        school = state.get("school")
        city = state.get("city")
        
        if email:
            try:
                # Save the CLEAN digits, not the messy user input
                save_lead(email, digits_only, school, city)
                print(f"✅ Lead Secured: {email} | {digits_only}")
            except Exception as e:
                print(f"⚠️ DB Save Warning: {e}")
        # ------------------------

        return {
            "messages": [AIMessage(content="Thanks! I've noted that. You can ask me **2 more questions** before we wrap up.")],
            "dialog_state": "chatting",
            "phone": digits_only # Save the clean number to state
        }
    else:
        # Failed validation
        return {
            "messages": [AIMessage(content="That doesn't look like a valid number. Please enter a valid **10-digit mobile number**.")],
            "dialog_state": "asking_phone" # Ask again
        }

def limit_exhausted_node(state: AgentState):
    email = state.get("email")
    phone = state.get("phone")
    school = state.get("school")
    city = state.get("city")
    
    # Save to DB (Safe Call)
    if email and phone:
        try:
            # Ensure your database.py accepts 4 arguments!
            save_lead(email, phone, school, city)
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