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
from langchain_community.document_loaders import DirectoryLoader, TextLoader # <--- CHANGED: For .txt files
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

PINECONE_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
DATA_PATH = "backend/data" # <--- CHANGED: Point to your text folder

# --- HIGH-VALUE PAGES ---
IMPORTANT_URLS = [
    "https://mhcockpit.com/",
    "https://mhcockpit.com/about-us/",
    "https://mhcockpit.com/pilot-training/",
    "https://mhcockpit.com/our-fleet/",
    "https://mhcockpit.com/contact-us/",
]

def setup_pinecone():
    """Check if index exists, create if not."""
    pc = Pinecone(api_key=PINECONE_KEY)
    existing_indexes = [i.name for i in pc.list_indexes()]
    
    if INDEX_NAME not in existing_indexes:
        print(f"Creating index: {INDEX_NAME}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(10) 
    else:
        print(f"Index {INDEX_NAME} already exists.")

def load_data():
    documents = []
    
    # --- PART 1: LOAD TEXT FILES (REPLACED PDF LOGIC) ---
    print(f"📂 Loading text files from '{DATA_PATH}'...")
    
    if os.path.exists(DATA_PATH):
        try:
            # DirectoryLoader helps load all files matching a pattern
            # glob="*.txt" ensures we only look for text files
            # We add 'loader_kwargs' to force UTF-8 encoding
            loader = DirectoryLoader(
                DATA_PATH, 
                glob="*.txt", 
                loader_cls=TextLoader, 
                loader_kwargs={'encoding': 'utf-8'}
            )
            text_docs = loader.load()
            
            if text_docs:
                for doc in text_docs:
                    # Add metadata so the bot knows where this came from
                    doc.metadata["source_type"] = "text_file"
                    # Clean up filename for logging
                    filename = os.path.basename(doc.metadata.get("source", "unknown"))
                    print(f"   ✅ Loaded: {filename}")
                
                documents.extend(text_docs)
            else:
                print("   ⚠️ No .txt files found in folder.")
                
        except Exception as e:
            print(f"   ❌ Error loading text files: {e}")
    else:
        print(f"   ❌ Directory '{DATA_PATH}' does not exist. Please create it.")

    # --- PART 2: LOAD WEBSITE (HEADLESS BROWSER) ---
    # (Kept intact as per your original code)
    print(f"Rendering {len(IMPORTANT_URLS)} pages with Playwright...")
    try:
        loader = AsyncChromiumLoader(IMPORTANT_URLS)
        html_docs = loader.load()
        
        html2text = Html2TextTransformer()
        web_docs = html2text.transform_documents(html_docs)
        
        for doc in web_docs:
            doc.metadata["source_type"] = "website_content"
            print(f" - Scraped {doc.metadata['source']}")
            
        documents.extend(web_docs)
        
    except Exception as e:
        print(f"Error loading website: {e}")
    
    return documents

def ingest_to_pinecone(documents):
    if not documents:
        print("No documents to ingest.")
        return

    # Use a smaller chunk size for text files to keep answers precise
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Total chunks to process: {len(chunks)}")

    print("Loading local embedding model (all-MiniLM-L6-v2)...")
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    print("Upserting to Pinecone...")
    try:
        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=INDEX_NAME
        )
        print("🎉 Ingestion Complete!")
    except Exception as e:
        print(f"❌ Pinecone Upload Error: {e}")

if __name__ == "__main__":
    setup_pinecone()
    raw_docs = load_data()
    ingest_to_pinecone(raw_docs)