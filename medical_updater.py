import os
import requests
import hashlib
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# ================= PATHS =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORY_PATH = os.path.join(BASE_DIR, "medical_data", "categories")
VECTOR_PATH = os.path.join(BASE_DIR, "vector_db")

os.makedirs(CATEGORY_PATH, exist_ok=True)

# ================= EMBEDDINGS =================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ================= LOAD VECTOR DB =================

vectorstore = Chroma(
    persist_directory=VECTOR_PATH,
    embedding_function=embeddings
)

# ================= MEDICAL CATEGORIES =================

MEDICAL_CATEGORIES = [
    "cardiology diseases overview",
    "infectious diseases overview",
    "neurology disorders overview",
    "respiratory diseases overview",
    "gastrointestinal diseases overview",
    "endocrine disorders overview",
    "mental health disorders overview",
    "bacterial infections overview",
    "viral diseases overview",
    "autoimmune diseases overview",
    "pediatric diseases overview",
    "emergency medicine protocols overview",
    "common medications overview",
    "vaccination guidelines WHO"
]

# ================= SEARCH FUNCTION =================

def search_trusted_sources(query):

    print(f"Searching trusted sources for: {query}")

    search_query = query + " site:who.int OR site:cdc.gov"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=5))
    except Exception as e:
        print("Search error:", e)
        return None

    for r in results:
        url = r.get("href") or r.get("url")

        if not url:
            continue

        try:
            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            soup = BeautifulSoup(response.text, "html.parser")

            paragraphs = soup.find_all("p")
            text_content = " ".join([p.get_text() for p in paragraphs])

            if len(text_content) > 1500:
                print("Content extracted successfully.")
                return text_content[:5000]  # limit size for safety

        except Exception:
            continue

    print("No valid content found.")
    return None

# ================= ADD TO VECTOR DB =================

def add_to_vector_db(content):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(content)
    documents = [Document(page_content=chunk) for chunk in chunks]

    vectorstore.add_documents(documents)
    vectorstore.persist()

# ================= CATEGORY UPDATE =================

def update_category(topic):

    print(f"\nUpdating category: {topic}")

    content = search_trusted_sources(topic)

    if not content:
        print("No content retrieved.")
        return

    filename_hash = hashlib.md5(topic.encode()).hexdigest()
    file_path = os.path.join(CATEGORY_PATH, f"{filename_hash}.txt")

    if os.path.exists(file_path):
        print("Already stored. Skipping.")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    add_to_vector_db(content)

    print("Category added to database successfully.")

# ================= MAIN =================

if __name__ == "__main__":

    print("\nStarting controlled medical knowledge expansion...\n")

    for topic in MEDICAL_CATEGORIES:
        update_category(topic)

    print("\nUpdate completed successfully.\n")