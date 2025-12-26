# ✈️ MH Cockpit - AI Flight Assistant

**MH Cockpit** is an intelligent conversational assistant designed to help with pilot training, aviation brochures, and fee structures. Powered by Google's **Gemini 1.5 Flash** model, it provides real-time responses to aviation-related queries.

## 🌟 Features

* **AI-Powered Conversations:** Utilizes the Gemini API for natural, context-aware responses.
* **User Onboarding:** Collects user email for personalized assistance.
* **Flight Deck Interface:** A clean, aviation-themed UI for pilot trainees.
* **Rate Limit Handling:** Optimized to handle API quotas efficiently.

## 🛠️ Tech Stack

* **Frontend:** <img width="1919" height="1000" alt="image" src="https://github.com/user-attachments/assets/0452b639-1551-4513-b07f-b886d774d251" />

* **Backend:** <img width="1919" height="1015" alt="image" src="https://github.com/user-attachments/assets/03c57f0c-a3e4-4813-8d6a-604ca6f2f0ce" />

* **AI Model:** Google Gemini 1.5 Flash

## 🚀 Getting Started

Follow these instructions to set up the project locally on your machine.

### Prerequisites

* Git
* Python 
* MongoDB
* A Google AI Studio API Key
* Pinecone API key

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Kopichino/Aviation-chatbot
    cd Aviation-chatbot
    ```

2.  **Install dependencies**
    ```bash
    # If using Node/React:
    npm install

    # If using Python:
    pip install -r requirements.txt
    ```

3.  **Environment Configuration (Crucial Step)**
    This project uses environment variables to keep API keys secure.
    
    * Create a new file in the root directory named `.env`
    * Add your Gemini API key to it:
    
    ```text
    GEMINI_API_KEY=your_actual_api_key_here
    ```
    
    * *Note: The `.env` file is git-ignored to protect your credentials.*

4.  **Run the Application**
    ```bash
    # To run backend
    uvicorn backend.main:api --reload
    # Open index2.html in live server
    ```

5. Admin Dashboard

The backend includes a built-in Admin Panel to view leads and chat history.

* **Access URL:** `http://127.0.0.1:8000/admin`
* **Features:**
    * View all collected leads (Name, Email, Phone, School, City).
    * **"View Chat" Button:** Opens a modal showing the full conversation history for that user.
    * Real-time updates (refresh page to see new leads).
      
    * **Admin Panel:**  <img width="1907" height="913" alt="image" src="https://github.com/user-attachments/assets/3b2a2832-a63e-4f0d-9f23-cef042a50fe6" />

      <img width="1911" height="911" alt="image" src="https://github.com/user-attachments/assets/fbdf36d6-48ce-40ca-b49c-65491f4fff3b" />

  
    * **MongoDB Compass:** <img width="1315" height="229" alt="image" src="https://github.com/user-attachments/assets/ef59a2b9-fe4d-4e09-8bda-cf1ca0180824" />


## 🤝 Contributing

Contributions are welcome!

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Created by Koppesh*
