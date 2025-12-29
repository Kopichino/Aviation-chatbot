# ☁️ AWS Deployment Guide: MH Cockpit Bot

This guide details how to deploy the **MH Cockpit Chatbot Backend** to a new AWS environment.

**Artifact Provided:** `deployment.zip` (Contains the pre-built Python 3.12 backend with Linux-compatible dependencies).

---

## ✅ Prerequisites

1.  **AWS Account Access** (Console access with Admin permissions).
2.  **API Keys** (You will need these values during setup):
    - `GOOGLE_API_KEY` (Gemini)
    - `PINECONE_API_KEY`
    - `PINECONE_INDEX_NAME`

---

## 📦 Step 1: Upload Code to S3

_Since the deployment package is >50MB, it cannot be uploaded directly to Lambda. We must use S3 as a bridge._

1.  Log in to the **AWS Console** and search for **S3**.
2.  Click **Create bucket**.
3.  **Bucket Name:** `mh-cockpit-deployment-[company-name]` (must be unique).
4.  **Region:** `ap-south-1` (Mumbai) - _Or your preferred region_.
5.  Click **Create bucket**.
6.  Open the newly created bucket.
7.  Click **Upload** -> Drag and drop the `deployment.zip` file.
8.  Click **Upload**.
9.  Once finished, click on the `deployment.zip` file name.
10. **Copy the "S3 URI"** (e.g., `s3://mh-cockpit-deployment/deployment.zip`). _Save this for Step 3._

---

## 🔑 Step 2: Create IAM Role (Permissions)

_The bot needs permission to write logs and access the internet._

1.  Search for **IAM** in the AWS Console.
2.  Go to **Roles** -> **Create role**.
3.  **Trusted entity type:** Select **AWS Service**.
4.  **Service or use case:** Select **Lambda**.
5.  Click **Next**.
6.  **Add permissions:** Search for and check these boxes:
    - `AWSLambdaBasicExecutionRole` (Required for logs).
7.  Click **Next**.
8.  **Role Name:** `MH-Cockpit-Lambda-Role`.
9.  Click **Create role**.

---

## 🚀 Step 3: Create the Lambda Function

1.  Search for **Lambda** in the AWS Console.
2.  Click **Create function**.
3.  **Select:** "Author from scratch".
4.  **Function Name:** `MH-Cockpit-Bot`.
5.  **Runtime:** **Python 3.12** (Crucial: Must match the build).
6.  **Architecture:** **x86_64**.
7.  **Permissions:**
    - Expand "Change default execution role".
    - Select **Use an existing role**.
    - Choose `MH-Cockpit-Lambda-Role` (created in Step 2).
8.  Click **Create function**.

---

## ⚙️ Step 4: Deploy the Code

1.  In the function overview, go to the **Code** tab.
2.  Click **Upload from** -> **Amazon S3 location**.
3.  Paste the **S3 URI** you copied in Step 1.
4.  Click **Save**.
    - _The editor will show "The deployment package of your Lambda function is too large to enable inline code editing." This is normal._

---

## 🔧 Step 5: Configuration & Environment Variables

1.  Go to the **Configuration** tab -> **Environment variables**.
2.  Click **Edit** -> **Add environment variable**.
3.  Add the following keys and your specific values:

| Key                   | Value               |
| :-------------------- | :------------------ |
| `GOOGLE_API_KEY`      | `AIzaSy...`         |
| `PINECONE_API_KEY`    | `pcsk_...`          |
| `PINECONE_INDEX_NAME` | `mh-aviation-index` |

4.  Click **Save**.

---

## 🌐 Step 6: Public Access (Function URL)

1.  Go to the **Configuration** tab -> **Function URL**.
2.  Click **Create function URL**.
3.  **Auth type:** Select **NONE** (Public API).
4.  **Additional settings (CORS):** **Enable this!**
    - **Allow origin:** `*`
    - **Allow headers:** `*`
    - **Allow methods:** `*`
5.  Click **Save**.
6.  Copy the **Function URL** provided (e.g., `https://...lambda-url...aws`).

---

## 🧪 Step 7: Verification

1.  **Test Admin Panel:**

    - Open `<FUNCTION_URL>/admin` in your browser.
    - You should see the "MH Cockpit Admin" interface.

2.  **Test Chat API:**
    - Send a POST request to `<FUNCTION_URL>/chat` with the JSON body:
    ```json
    {
      "message": "Hello",
      "session_id": "test-1"
    }
    ```

**Deployment Complete! 🚀**

# 💻 Frontend Integration Guide: MH Cockpit Chatbot

This document outlines the steps to integrate the deployed MH Cockpit Chatbot backend with the company's frontend application.

---

## 📋 1. Prerequisites

Before starting, ensure you have the **Function URL** from the backend deployment team.

- **Base URL Example:** `https://xyz123.lambda-url.ap-south-1.on.aws`
- **Auth:** Public (No bearer tokens required)
- **CORS:** Enabled for all origins (`*`)

---

## 🔗 2. API Specification

### Chat Endpoint

- **API-for-CHAT:** `/api/leads`
- **URL:** `POST /chat`
- **Content-Type:** `application/json`

---

### Request Payload

The `session_id` is **critical**. It persists the conversation context (memory) for the user.

```json
{
  "message": "User's question string",
  "session_id": "unique-user-session-id"
}
```

---

### Response Payload (Success - 200 OK)

```json
{
  "response": "The bot's answer text...",
  "source_documents": [
    { "page_content": "Reference text used..." },
    { "page_content": "More reference text..." }
  ]
}
```

---

### Error Payload (422 Unprocessable Entity)

Occurs if session_id is missing.

```json
{
  "detail": [{ "msg": "field required", "type": "value_error.missing" }]
}
```

---

## 🛠️ 3. Implementation Steps

### Step A: Session Management

You must generate or retrieve a unique ID for the user.

- **Logged-in Users:** Use their Database User ID.
- **Guest Users:** Generate a UUID on app load and store it in localStorage.

Example (Helper function):

```javascript
import { v4 as uuidv4 } from "uuid"; // npm install uuid

const getSessionId = () => {
  let sessionId = localStorage.getItem("chat_session_id");
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem("chat_session_id", sessionId);
  }
  return sessionId;
};
```

---

### Step B: API Service Function

Create a dedicated service file (e.g., `api/chatbot.js`) to handle requests.

```javascript
// api/chatbot.js

// TODO: Replace with the actual deployed URL
const BASE_URL = "https://YOUR-LAMBDA-URL.lambda-url.ap-south-1.on.aws";

/**
 * Sends a message to the chatbot.
 * @param {string} message - The user's input.
 * @param {string} sessionId - Unique session ID.
 * @returns {Promise<Object>} - The bot's response object.
 */
export const sendMessageToBot = async (message, sessionId) => {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.detail?.[0]?.msg || "Network response was not ok"
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Chatbot API Error:", error);
    throw error;
  }
};
```

---

### Step C: Integrating into React Component

Here is a simplified example of how to connect the UI to the service.

```javascript
import React, { useState, useEffect } from "react";
import { sendMessageToBot } from "./api/chatbot";
import { getSessionId } from "./utils/session"; // Helper from Step A

const ChatWidget = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    // 1. Add user message to UI immediately
    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setInput("");

    try {
      // 2. Call API
      const data = await sendMessageToBot(userMsg.text, sessionId);

      // 3. Add bot response to UI
      const botMsg = { sender: "bot", text: data.response };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      const errorMsg = {
        sender: "bot",
        text: "Sorry, I encountered an error.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-list">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="loader">Bot is thinking...</div>}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWidget;
```

---

## 💡 4. UX & Best Practices

### Cold Start Handling

Since the backend runs on Serverless AWS Lambda, the first request after inactivity may take **3–5 seconds**.

**Recommendation:** Display a "Connecting..." or "Thinking..." typing indicator during loading.

---

### Markdown Rendering

The bot may return responses with Markdown formatting (bolding, lists, code blocks).

**Recommendation:** Use a library like `react-markdown` to render the bot's response properly.

---

### Persisting History

The backend remembers context, but it does not return the full chat history on every call.

**Recommendation:** The frontend should store messages in component state (or Redux/Context).

---

## 🧪 5. Testing & Debugging

- To verify connection: Open **Developer Tools → Network Tab**. Look for the request to `/chat`.
- To reset context: Generate a new `session_id` (or clear `localStorage`).
- This makes the bot "forget" previous conversation state.
