# 🚀 Backend API Documentation: MH Cockpit Bot

**Status:** Live on AWS Lambda (Serverless)  
**Region:** `ap-south-1` (Asia Pacific - Mumbai)  
**Auth:** Public (No Bearer Token required)

## 🌐 Base URL

```text
https://apkdqiny4lxrbjwpi5m7wl2s4i0mdgfc.lambda-url.ap-south-1.on.aws
```

## 📡 Endpoints

### 1. Chat Interface

This is the main endpoint for the chatbot. It connects to the Pinecone Vector DB and Gemini LLM.

- **Endpoint:** `POST /chat`
- **Content-Type:** `application/json`

#### **Request Body (JSON)**

The `session_id` is **mandatory**. It allows the bot to remember context (e.g., previous questions) for that specific user.

```json
{
  "message": "User's question goes here",
  "session_id": "unique-string-for-user"
}
```

> **Frontend Tip:** Generate a unique `session_id` (like a UUID) when the user opens the app, or use their actual User ID. Keep it consistent for the duration of the session.

#### **Response Example (200 OK)**

```json
{
  "response": "MH Cockpit offers three tiers of pilot training programs...",
  "source_documents": [{ "page_content": "..." }]
}
```

#### **Error Example (422 Unprocessable Entity)**

```markdown
Occurs if `session_id` is missing.
```

```json
{
  "detail": [
    {
      "loc": ["body", "session_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 2. Admin Dashboard

```markdown
A visual interface to view the backend status.
```

- **Endpoint:** `GET /admin`
- **Access:** Open in Browser
- **URL:** `https://apkdqiny4lxrbjwpi5m7wl2s4i0mdgfc.lambda-url.ap-south-1.on.aws/admin`

## 💻 Usage Example (JavaScript/Fetch)

```javascript
const sendMessage = async (userMessage, sessionId) => {
  const url =
    "https://apkdqiny4lxrbjwpi5m7wl2s4i0mdgfc.lambda-url.ap-south-1.on.aws/chat";

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        session_id: sessionId,
      }),
    });

    const data = await res.json();
    console.log("Bot says:", data.response);
    return data;
  } catch (error) {
    console.error("API Error:", error);
  }
};
```

## ⚙️ Backend Deployment Guide (How to Update)

**⚠️ Important:** The backend runs on **AWS Lambda** (Python 3.12). The deployment package is >50MB, so you **cannot** upload it directly to Lambda. You must use Amazon S3.

### Prerequisites

1.  **`deployment.zip`**: The zipped backend code (including all Linux-compatible libraries).
2.  **AWS Access**: Permissions to access S3 and Lambda in `ap-south-1`.

### Step-by-Step Deployment

#### 1. Upload to S3

- Go to the **Amazon S3 Console**.
- Open the deployment bucket (e.g., `mh-aviation-deploy`).
- Click **Upload** -> Drag & Drop your new `deployment.zip`.
- Once uploaded, click the file name and copy the **S3 URI** (e.g., `s3://mh-aviation-deploy/deployment.zip`).

#### 2. Update Lambda

- Go to the **AWS Lambda Console**.
- Open the function: **`MH-Cockpit-Bot`**.
- Go to the **Code** tab.
- Click **Upload from** -> **Amazon S3 location**.
- Paste the **S3 URI** you copied earlier.
- Click **Save**.

#### 3. Verify

- Visit the Admin URL (`/admin`) to ensure the server is running.
- If you see "Internal Server Error," check **CloudWatch Logs** via the Monitor tab.
