import requests
import time
import random

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000/chat"
SESSION_ID = f"strict-test-{random.randint(1000, 9999)}"

def send_request(message, step_description):
    print(f"\n🔹 {step_description}")
    print(f"   📤 Sending: '{message}'")
    
    payload = {
        "message": message,
        "session_id": SESSION_ID
    }
    
    try:
        response = requests.post(BASE_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        bot_reply = data.get("response", "No response text")
        
        print(f"   🤖 Bot: {bot_reply}")
        return bot_reply
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# ==========================================
# 🚀 START AUTOMATED TEST (SLOW MODE)
# ==========================================
print(f"🚀 STARTING SLOW TEST (Session: {SESSION_ID})")
print("------------------------------------------------------")

# --- STEP 1: EMAIL COLLECTION ---
send_request("Hi", "Step 1: Start Chat")
time.sleep(5) # Wait 5 seconds

send_request(f"tester{random.randint(10,99)}@example.com", "Step 2: Provide Email")
time.sleep(5)

# --- STEP 2: GUEST MODE (3 Queries) ---
send_request("What courses do you offer?", "Step 3: Guest Query 1")
time.sleep(10) # Increasing wait time for Gemini Embeddings

send_request("Where is the campus?", "Step 4: Guest Query 2")
time.sleep(10)

send_request("Do you have hostel facility?", "Step 5: Guest Query 3")
time.sleep(10)

# --- STEP 3: TRIGGER REGISTRATION ---
print("\n--- EXPECTATION: Bot should ask for details ---")
send_request("What is the fee structure?", "Step 6: Guest Query 4 (Trigger)")
time.sleep(5)

# --- STEP 4: TEST FORMAT VALIDATION ---
send_request("My name is Rahul and I am from DPS", "Step 7: Sending Invalid Format")
time.sleep(5)

print("\n--- EXPECTATION: Bot should accept this ---")
send_request("Rahul, DPS, Chennai, 9876543210", "Step 8: Sending CORRECT Format")
time.sleep(5)

# --- STEP 5: REGISTERED MODE (6 Queries) ---
print("\n--- PHASE: Registered User (Testing Limit of 6) ---")
queries = [
    "What is the duration of CPL?",
    "Do you offer ground classes?",
    "Is the academy DGCA approved?",
    "Who are the instructors?",
    "What is the age limit?",
    "Can I join after 12th?"
]

for i, q in enumerate(queries):
    send_request(q, f"Step {9+i}: Reg Query {i+1}")
    # CRITICAL: Wait 15 seconds between RAG queries to respect Free Tier Limits
    print("   ⏳ Waiting 15s to avoid Rate Limit...")
    time.sleep(15) 

# --- STEP 6: LIMIT EXHAUSTED ---
print("\n--- EXPECTATION: Bot should BLOCK this query ---")
send_request("This should fail.", "Step 15: Final Query (Limit Test)")

print("\n✅ Test Complete.")