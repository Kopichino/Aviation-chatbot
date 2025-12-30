# ✈️ MH Cockpit Aviation Chatbot - Backend Deployment Guide

This repository contains the serverless backend for the MH Cockpit Aviation Chatbot. It is built using **FastAPI**, **LangChain**, **Google Gemini**, **Pinecone**, and **AWS DynamoDB**.

The system is designed to be deployed on **AWS Lambda** (Python 3.12).

---

## ✅ Prerequisites

Before deployment, ensure you have access to the **Company AWS Console** with permissions for:

- **Lambda** (Create/Update functions)
- **S3** (Upload large files)
- **DynamoDB** (Create tables)
- **IAM** (Manage roles/permissions)

### Required API Keys

You will need these keys ready for the configuration step:

1.  **`GOOGLE_API_KEY`**: (Google AI Studio Key for Gemini)
2.  **`PINECONE_API_KEY`**: (Pinecone Vector DB Key)
3.  **`PINECONE_INDEX_NAME`**: (Name of your vector index)

---

## 🚀 Phase 1: Infrastructure Setup

### 1. Create DynamoDB Table

- **Service:** DynamoDB
- **Table Name:** `MH_Aviation_Leads` (Case-sensitive!)
- **Partition Key:** `email` (String)
- **Sort Key:** _None_
- **Settings:** "On-demand" capacity mode is recommended.

### 2. Create S3 Bucket (For Deployment Artifacts)

- **Service:** S3
- **Bucket Name:** e.g., `mh-cockpit-deployment-assets`
- **Purpose:** The deployment zip file is too large (>50MB) to upload directly to Lambda. We must upload to S3 first.

---

## 🛠️ Phase 2: Building the Deployment Package

**Note:** AWS Lambda runs on Linux. If you are building on Windows, you **MUST** use the specific command below to install Linux-compatible libraries.

1.  **Navigate to the project root:**

    ```bash
    cd aviation-chatbot
    ```

2.  **Clean previous builds (if any):**
    Delete the `package` folder and `deployment.zip` if they exist.

3.  **Create a new package folder:**

    ```bash
    mkdir package
    ```

4.  **The "Magic" Install Command (Windows Powershell):**
    This installs Python 3.12 Linux-compatible wheels into the `package` folder.

    ```powershell
    pip install -r requirements.txt --target ./package --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all: --upgrade
    ```

5.  **Copy Backend Code:**
    Copy the entire `backend/` folder and paste it **inside** the `package/` folder.

6.  **Zip the Contents:**
    - Go **inside** the `package/` folder.
    - Select All (`backend/` folder + all library folders).
    - Right-click -> **Compress to Zip**.
    - Name it `deployment.zip`.

---

## ☁️ Phase 3: AWS Lambda Deployment

1.  **Upload to S3:**

    - Upload `deployment.zip` to your S3 bucket.
    - Copy the **S3 URI** (e.g., `s3://mh-cockpit-assets/deployment.zip`).

2.  **Create Lambda Function:**

    - **Function Name:** `aviation-chatbot-backend`
    - **Runtime:** **Python 3.12**
    - **Architecture:** **x86_64**
    - **Execution Role:** Create a new role with basic Lambda permissions.

3.  **Deploy Code:**

    - In the Lambda dashboard, click **Upload from** -> **Amazon S3 Location**.
    - Paste the S3 URI.

4.  **Configure Runtime Settings:**

    - Scroll down to "Runtime settings".
    - **Handler:** `backend.main.handler`
    - _(Crucial: If this is wrong, the bot will not start)_

5.  **Increase Timeout:**
    - Go to **Configuration** -> **General configuration** -> **Edit**.
    - Change Timeout from `3 sec` to **`1 min 0 sec`**.
    - _(AI models take time; 3 seconds is too short)_.

---

## 🔑 Phase 4: Environment & Permissions

### 1. Environment Variables

Go to **Configuration** -> **Environment variables** and add:

| Key                   | Value                         |
| :-------------------- | :---------------------------- |
| `GOOGLE_API_KEY`      | `AIzaSy...` (Your Key)        |
| `PINECONE_API_KEY`    | `pcsk_...` (Your Key)         |
| `PINECONE_INDEX_NAME` | `mh-aviation-index`           |
| `AWS_DEFAULT_REGION`  | `ap-south-1` (or your region) |

### 2. IAM Permissions (DynamoDB Access)

The Lambda function needs permission to read/write to the database.

1.  Go to **Configuration** -> **Permissions**.
2.  Click the **Role Name** to open IAM.
3.  Click **Add permissions** -> **Attach policies**.
4.  Search for and add: `AmazonDynamoDBFullAccess`.

---

## 🌐 Phase 5: Enable Function URL

1.  Go to **Configuration** -> **Function URL**.
2.  Click **Create function URL**.
3.  **Auth type:** `NONE` (Public API).
4.  **CORS:** Click "Configure cross-origin resource sharing (CORS)".
    - **Allow origin:** `*`
    - **Allow headers:** `*`
    - **Allow methods:** `*`
5.  Save.

**🎉 You now have your Backend URL!**
It will look like: `https://<random-id>.lambda-url.ap-south-1.on.aws/`

---

## 🔌 Phase 6: Frontend Integration

Provide the Backend URL to the Frontend/React team.

- **Chat Endpoint:** `POST <URL>/chat`
- **Admin Dashboard:** `GET <URL>/admin`
- **JSON chat API:** `GET <URL>/api/leads`

**Example Usage (JS):**

```javascript
const API_URL = "https://<your-id>.lambda-url.ap-south-1.on.aws/chat";

await fetch(API_URL, {
  method: "POST",
  body: JSON.stringify({
    message: "Hello",
    session_id: "user_123",
  }),
});
```
