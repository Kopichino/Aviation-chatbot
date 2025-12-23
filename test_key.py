from langchain_google_genai import ChatGoogleGenerativeAI

# PASTE YOUR NEW KEY DIRECTLY INSIDE THE QUOTES BELOW:
api_key = "____" 

try:
    print(f"Testing Key: {api_key[:5]}...")
    
    # We use 'gemini-1.5-flash-latest' because the standard name gave you a 404
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=api_key
    )
    response = llm.invoke("Hello, are you working?")
    print("\n✅ SUCCESS! The bot answered:")
    print(response.content)

except Exception as e:
    print("\n❌ FAILURE.")
    print(f"Error: {e}")