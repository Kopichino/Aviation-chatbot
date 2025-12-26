# 🚀 Backend Integration & Production Guide

### MH Cockpit Aviation Chatbot

This repository contains the **FastAPI Backend**, **AI Logic** (LangChain + Gemini + Pinecone), and **Database Layer** (MongoDB) for the MH Cockpit Chatbot.

---

## 🛠️ 1. Prerequisites & Setup

Ensure the host machine (server) has the following installed:

1.  **Python 3.10+**
2.  **MongoDB Community Server** (running on port `27017` by default)

### **Installation**

1.  Clone this repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    python -m pip install -r requirements.txt #if facing error with above
    ```

---

## 🔑 2. Environment Variables (.env)

Create a file named `.env` in the root directory. This file **must not** be committed to Git. Share these keys securely with the DevOps/Deployment team.

**Template:**

```ini
# --- AI & LLM CONFIGURATION ---
# Get this from Google AI Studio
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Get this from Pinecone Console
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=mh-aviation-index

# --- DATABASE CONFIGURATION ---
# Default local URI. For production (Atlas/Cloud), replace with the full connection string.
MONGO_URI=mongodb://localhost:27017/
DB_NAME=mh_aviation_db
```

---

## 📚 3. Knowledge Base Setup (RAG)

Before running the server, you must populate the Pinecone Vector Database with your knowledge documents.

1.  **Prepare Data:** Place all your reference documents (e.g., `fees.txt`, `courses.txt`, `brochure.txt`) inside the `backend/data/` folder.
2.  **Run Ingestion Script:**
    This script reads the `.txt` files, chunks them, generates embeddings, and uploads them to Pinecone.
    ```bash
    python scripts/ingest.py
    ```
    _Wait for the "🎉 Ingestion Complete!" message._

---

## 🏃 4. Running the Server

### **Option A: Development (Local)**

Auto-reloads when code changes.

```bash
uvicorn backend.main:api --reload --port 8000
```

- **API URL:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`

### **Option B: Serverless Production (AWS Lambda - Zip Upload)**

You can run the entire application (Chat + Admin) on a single AWS Lambda function without Docker by uploading a zipped package.

#### **Step 1: Prepare the Code**

1.  Add `mangum` to your `requirements.txt`:
    ```text
    mangum
    ```
2.  Update `backend/main.py` to add the Lambda handler at the bottom:
    ```python
    from mangum import Mangum
    # ... existing code ...
    api = FastAPI()
    # ... existing code ...
    handler = Mangum(api) # Entry point for AWS Lambda
    ```

#### **Step 2: Create the Deployment Package**

Since AWS Lambda doesn't install libraries automatically, you must bundle them with your code.

1.  **Create a folder for dependencies:**
    ```bash
    mkdir package
    ```
2.  **Install libraries into that folder:**
    ```bash
    pip install --target ./package -r requirements.txt
    ```
3.  **Create the Zip file:**
    - Go into the `package` folder and zip the contents (not the folder itself).
    - Add your project code (`backend/`, `templates/`, `main.py`) to the **root** of that same zip file.
    - Name it `deployment.zip`.

#### **Step 3: Upload to AWS Lambda**

1.  Go to **AWS Console > Lambda > Create Function**.
2.  Select **Author from scratch**.
3.  Runtime: **Python 3.10** or **3.11**.
4.  **Upload Code:**
    - If the Zip is < 50MB: Upload directly in the "Code" tab.
    - If the Zip is > 50MB: Upload the file to **AWS S3** first, then paste the S3 Link in Lambda.
5.  **Handler Settings:**
    - Click "Edit" on Runtime Settings.
    - Set Handler to: `backend.main.handler`.

#### **Step 4: Configuration**

1.  **General Configuration:**
    - **Timeout:** Increase to `60 seconds`.
    - **Memory:** Increase to `512MB` (recommended for AI processing).
2.  **Environment Variables:**
    - Add `GOOGLE_API_KEY`, `PINECONE_API_KEY`, etc.
3.  **Function URL:**
    - Go to the "Function URL" tab and click **Create function URL**.
    - Auth type: `NONE` (for public access).
    - This generates your **Base URL** (e.g., `https://xyz123.lambda-url.us-east-1.on.aws`).

---

## 📡 5. API Contract (For Frontend Team)

### **Endpoint: Chat with AI**

- **URL:** `POST /chat`
- **Content-Type:** `application/json`

**Request Body:**

```json
{
  "message": "Hi, I want to become a pilot.",
  "session_id": "unique_user_id_12345"
}
```

_Note: `session_id` must remain constant for the same user to maintain conversation memory._

**Response Body:**

```json
{
  "response": "Welcome! To assist you with brochures, could you please share your **email address**?"
}
```

### **JavaScript Integration Example (Fetch):**

```javascript
const response = await fetch(
  "[https://your-api-domain.com/chat](https://your-api-domain.com/chat)",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: "Tell me about CPL fees",
      session_id: localStorage.getItem("session_id") || "new_id",
    }),
  }
);
const data = await response.json();
console.log(data.response); // Display this in the chat bubble
```

---

## 📊 6. Admin Dashboard

The Admin Panel is hosted on the **same Lambda instance** as the chat API. No separate server is required.

### **Endpoints**

| Component      | HTTP Method | Endpoint URL | Description                    |
| :------------- | :---------- | :----------- | :----------------------------- |
| **Chat API**   | `POST`      | `/chat`      | Returns AI responses (JSON)    |
| **Admin UI**   | `GET`       | `/admin`     | Renders the Dashboard (HTML)   |
| **Leads Data** | `GET`       | `/api/leads` | Fetches raw data for the table |

### **How to Access**

If your Lambda Function URL is:
`https://xyz123.lambda-url.us-east-1.on.aws`

Then your Admin Panel URL is:
👉 **`https://xyz123.lambda-url.us-east-1.on.aws/admin`**

### **Features**

- View all collected leads (Name, Email, Phone, School, City).
- **"View Chat" Button:** Opens a modal showing the full conversation history for that user.
- Real-time updates (refresh page to see new leads).

---

## ⚠️ 7. Production Checklist

1.  **Database Validation:**
    - Ensure `backend/apply_validation.py` has been run **once** on the production MongoDB instance to enforce data rules (Email regex, Phone digits).
2.  **HTTPS:**
    - The API should sit behind a reverse proxy (Nginx/Apache) with SSL (HTTPS) enabled.
3.  **CORS:**

    - If the frontend is on a different domain (e.g., `frontend.com` vs `api.backend.com`), update `backend/main.py` to allow CORS:

    ```python
    from fastapi.middleware.cors import CORSMiddleware

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["[https://your-frontend-domain.com](https://your-frontend-domain.com)"], # Update this!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

---

## 📂 8. Project Structure

```text
/
├── backend/
│   ├── main.py            # API Entry Point
│   ├── chatbot_graph.py   # LangGraph Logic (State Machine)
│   ├── mongo_db.py        # Database Operations
│   ├── apply_validation.py # One-time DB Setup Script
│   └──data/           # Put new .txt files here for RAG
├── templates/
│   └── admin.html         # Admin Dashboard UI
├── scripts/
│   └── ingest.py          # Run this to update AI Knowledge (RAG)
├── requirements.txt       # Python Dependencies
└── .env                   # Secrets (DO NOT COMMIT)

```

---

## 🆘 Appendix: Setting up MongoDB Atlas (Required for AWS)

**Critical:** You cannot use `mongodb://localhost:27017` when deploying to AWS Lambda, because the cloud function does not have a database running inside it. You must use a cloud database.

### Step 1: Create the Cloud Database

1.  Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and sign up (it's free).
2.  Create a new project and select **Build a Database**.
3.  Choose the **M0 (Free)** tier and click **Create**.

### Step 2: Configure Security (Crucial for Lambda)

AWS Lambda uses rotating IP addresses, so you cannot whitelist a single IP.

1.  Go to **Network Access** (left sidebar).
2.  Click **Add IP Address**.
3.  Select **Allow Access from Anywhere** (`0.0.0.0/0`).
4.  Click **Confirm**.

### Step 3: Create a Database User

1.  Go to **Database Access** (left sidebar).
2.  Click **Add New Database User**.
3.  Create a username (e.g., `admin`) and a **strong password**.
    - _Save this password! You will need it in Step 5._
4.  Click **Add User**.

### Step 4: Get the Connection String

1.  Go to **Database** (left sidebar) and click **Connect** on your cluster.
2.  Select **Drivers**.
3.  Choose **Python** (Version 3.12 or later).
4.  Copy the connection string. It will look like this:
    ```text
    mongodb+srv://admin:<db_password>@cluster0.abcd.mongodb.net/?retryWrites=true&w=majority
    ```

### Step 5: Update Your Code

Ensure your `backend/mongo_db.py` is updated to read from environment variables instead of hardcoding localhost.

**Update `backend/mongo_db.py`:**

```python
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Get the URI from environment variables
uri = os.getenv("MONGO_URI")

# Fallback to localhost ONLY if no URI is found (for local testing)
if not uri:
    print("⚠️ Using Localhost MongoDB")
    uri = "mongodb://localhost:27017/"

client = MongoClient(uri)
db = client["mh_aviation_db"]
# ... rest of your code
```

### Step 6: Add to Environment

1.  **Local Testing:** Update your `.env` file:
    ```ini
    MONGO_URI=mongodb+srv://admin:your_real_password@cluster0.abcd.mongodb.net/?retryWrites=true&w=majority
    ```
2.  **Production (AWS):** Go to your Lambda function -> **Configuration** -> **Environment variables** and add `MONGO_URI` there.
