import os
import time
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# --- CONFIGURATION ---
# Make sure your .env file has your keys!
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PINECONE_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "mh-aviation-index") # Default name
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")

# --- 1. SETUP CONNECTION ---
print(f"🔌 Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_KEY)

# --- 2. DELETE OLD INDEX (THE FIX) ---
if INDEX_NAME in [i.name for i in pc.list_indexes()]:
    print(f"🗑️  Found old index '{INDEX_NAME}'. Deleting...")
    pc.delete_index(INDEX_NAME)
    print("⏳ Waiting 10 seconds for deletion to finish...")
    time.sleep(10)
else:
    print(f"✨ Index '{INDEX_NAME}' does not exist yet.")

# --- 3. CREATE NEW INDEX (DIMENSION 768) ---
print(f"🔨 Creating new index '{INDEX_NAME}' with Dimension 768 (Google)...")
pc.create_index(
    name=INDEX_NAME,
    dimension=768, # <--- CRITICAL: 768 is for Google Gemini. (384 is for HuggingFace)
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1") # Change region if needed
)
print("✅ Index created successfully!")

# --- 4. RE-UPLOAD DATA (So bot isn't empty) ---
print("📂 Loading PDF data...")
# REPLACE 'data/brochure.pdf' WITH YOUR ACTUAL FILE PATH
pdf_path = "data/brochure.pdf" 

if os.path.exists(pdf_path):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = splitter.split_documents(docs)
    print(f"📄 Split PDF into {len(splits)} chunks.")

    print("🚀 Generating Embeddings & Uploading (This may take a moment)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # Batch upload to avoid timeouts
    PineconeVectorStore.from_documents(
        documents=splits,
        embedding=embeddings,
        index_name=INDEX_NAME
    )
    print("🎉 SUCCESS: Database reset and repopulated!")
else:
    print(f"⚠️ WARNING: Could not find '{pdf_path}'. Index is created but EMPTY.")
    print("   Please put your PDF in the folder and run the upload separately.")