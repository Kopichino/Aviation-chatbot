# import os
# import time
# from dotenv import load_dotenv

# # Loaders
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.document_loaders import AsyncChromiumLoader # <--- NEW: Headless Browser
# from langchain_community.document_transformers import Html2TextTransformer # <--- NEW: Cleans the HTML

# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from pinecone import Pinecone, ServerlessSpec

# load_dotenv()

# PINECONE_KEY = os.getenv("PINECONE_API_KEY")
# INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# # --- HIGH-VALUE PAGES ---
# IMPORTANT_URLS = [
#     "https://mhcockpit.com/",
#     "https://mhcockpit.com/about-us/",
#     "https://mhcockpit.com/pilot-training/",
#     "https://mhcockpit.com/our-fleet/",
#     "https://mhcockpit.com/contact-us/",
# ]

# def setup_pinecone():
#     """Check if index exists, create if not."""
#     pc = Pinecone(api_key=PINECONE_KEY)
#     existing_indexes = [i.name for i in pc.list_indexes()]
    
#     if INDEX_NAME not in existing_indexes:
#         print(f"Creating index: {INDEX_NAME}...")
#         pc.create_index(
#             name=INDEX_NAME,
#             dimension=384,
#             metric="cosine",
#             spec=ServerlessSpec(cloud="aws", region="us-east-1")
#         )
#         time.sleep(10) 
#     else:
#         print(f"Index {INDEX_NAME} already exists.")

# def load_data():
#     documents = []
    
#     # --- PART 1: LOAD PDFs ---
#     data_folder = "data"
#     if os.path.exists(data_folder):
#         for file in os.listdir(data_folder):
#             if file.endswith(".pdf"):
#                 pdf_path = os.path.join(data_folder, file)
#                 print(f"Loading PDF: {file}...")
#                 try:
#                     loader = PyPDFLoader(pdf_path)
#                     docs = loader.load()
#                     for doc in docs:
#                         doc.metadata["source_type"] = "brochure"
#                         doc.metadata["source"] = file
#                     documents.extend(docs)
#                 except Exception as e:
#                     print(f"Error loading PDF {file}: {e}")

#     # --- PART 2: LOAD WEBSITE (HEADLESS BROWSER) ---
#     print(f"Rendering {len(IMPORTANT_URLS)} pages with Playwright (this takes time)...")
#     try:
#         # 1. Load raw HTML using a real browser
#         loader = AsyncChromiumLoader(IMPORTANT_URLS)
#         html_docs = loader.load()
        
#         # 2. Transform HTML to clean text
#         html2text = Html2TextTransformer()
#         web_docs = html2text.transform_documents(html_docs)
        
#         for doc in web_docs:
#             doc.metadata["source_type"] = "website_content"
#             # Print snippet to debug
#             print(f" - Scraped {doc.metadata['source']}: Found {len(doc.page_content)} characters.")
            
#         documents.extend(web_docs)
        
#     except Exception as e:
#         print(f"Error loading website: {e}")
    
#     return documents

# def ingest_to_pinecone(documents):
#     if not documents:
#         print("No documents to ingest.")
#         return

#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     chunks = text_splitter.split_documents(documents)
#     print(f"Total chunks to process: {len(chunks)}")

#     print("Loading local embedding model (all-MiniLM-L6-v2)...")
#     embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
#     print("Upserting to Pinecone...")
#     PineconeVectorStore.from_documents(
#         documents=chunks,
#         embedding=embeddings,
#         index_name=INDEX_NAME
#     )
#     print("Ingestion Complete!")

# if __name__ == "__main__":
#     setup_pinecone()
#     raw_docs = load_data()
#     ingest_to_pinecone(raw_docs)

import os
import time
from dotenv import load_dotenv

# Loaders
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

# 1. SETUP
load_dotenv()
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
DATA_PATH = "backend/data"

IMPORTANT_URLS = [
    "https://mhcockpit.com/",
    "https://mhcockpit.com/about-us/",
    "https://mhcockpit.com/pilot-training/",
    "https://mhcockpit.com/our-fleet/",
    "https://mhcockpit.com/contact-us/",
]

def setup_pinecone():
    pc = Pinecone(api_key=PINECONE_KEY)
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        print(f"🔨 Creating index '{INDEX_NAME}' (Dim: 768)...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=768, 
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(10)

def load_all_docs():
    docs = []
    # Text Files
    if os.path.exists(DATA_PATH):
        try:
            loader = DirectoryLoader(DATA_PATH, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
            docs.extend(loader.load())
        except: pass
    
    # Websites
    try:
        loader = AsyncChromiumLoader(IMPORTANT_URLS)
        html_docs = loader.load()
        html2text = Html2TextTransformer()
        docs.extend(html2text.transform_documents(html_docs))
    except: pass
    
    return docs

def turtle_upload(documents):
    if not documents: return

    # Split Data
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    total = len(chunks)
    print(f"🐢 TURTLE MODE: Processing {total} chunks...")
    print("✨ Using Model: text-embedding-004 (New Quota Bucket)")

    # --- CRITICAL CHANGE: USE NEW MODEL ---
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    # --------------------------------------
    
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

    # LOOP 1-BY-1
    for i, chunk in enumerate(chunks):
        success = False
        while not success:
            try:
                print(f"📤 Uploading {i+1}/{total}...", end=" ")
                vector_store.add_documents([chunk])
                print("✅ Done. Waiting 5s...")
                success = True
                time.sleep(5) # Faster wait time for new model
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("⚠️ HIT RATE LIMIT. Waiting 60s...")
                time.sleep(60)

if __name__ == "__main__":
    setup_pinecone()
    raw_docs = load_all_docs()
    turtle_upload(raw_docs)