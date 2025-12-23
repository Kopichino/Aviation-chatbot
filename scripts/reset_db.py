import os
import time
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

pc = Pinecone(api_key=PINECONE_KEY)

# Check if index exists and DELETE it
if INDEX_NAME in [i.name for i in pc.list_indexes()]:
    print(f"Deleting old index '{INDEX_NAME}' (Dimension: 1536)...")
    pc.delete_index(INDEX_NAME)
    print("Deleted! Waiting 20 seconds for Pinecone to reset...")
    time.sleep(20) # Essential wait time
else:
    print(f"Index '{INDEX_NAME}' does not exist. You are good to go.")

print("Ready for ingestion.")