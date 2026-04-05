import os
import requests
import hashlib
from bs4 import BeautifulSoup
from ddgs import DDGS

from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


# ================= PATHS =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEXT_PATH = os.path.join(BASE_DIR, "medical_data", "clinical_text")
CACHE_PATH = os.path.join(BASE_DIR, "medical_data", "auto_cache")
VECTOR_PATH = os.path.join(BASE_DIR, "vector_db")

os.makedirs(CACHE_PATH, exist_ok=True)


# ================= EMBEDDINGS =================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ================= LOAD OR CREATE VECTOR DB =================

if os.path.exists(VECTOR_PATH) and os.listdir(VECTOR_PATH):

    print("Loading existing vector database...")

    vectorstore = Chroma(
        persist_directory=VECTOR_PATH,
        embedding_function=embeddings
    )

else:

    print("Creating new vector database...")

    documents = []

    if os.path.exists(TEXT_PATH):
        loader = DirectoryLoader(TEXT_PATH, glob="**/*.txt", loader_cls=TextLoader)
        documents.extend(loader.load())

    if os.path.exists(CACHE_PATH):
        loader = DirectoryLoader(CACHE_PATH, glob="**/*.txt", loader_cls=TextLoader)
        documents.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    docs = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=VECTOR_PATH
    )

    vectorstore.persist()


# ================= LLM =================

llm = OllamaLLM(
    model="OussamaELALLAM/AtlasMed-R1",
    temperature=0.2
)


# ================= UTILITIES =================

def clean_response(text):
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text.strip()


def classify_risk(text):

    s = text.lower()

    if "chest pain" in s or "breathing difficulty" in s:
        return "EMERGENCY"

    if "severe bleeding" in s or "unconscious" in s:
        return "HIGH"

    if "fever" in s or "pain" in s:
        return "MODERATE"

    return "LOW"


# ================= TRUSTED WEB SEARCH =================

def search_trusted_medical_sources(query):

    search_query = query + " site:who.int OR site:cdc.gov"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=5))
    except:
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

            if len(text_content) > 1200:
                return text_content[:5000]

        except:
            continue

    return None


# ================= CACHE WEB DATA =================

def cache_web_data(query, content):

    filename_hash = hashlib.md5(query.encode()).hexdigest()

    file_path = os.path.join(CACHE_PATH, f"{filename_hash}.txt")

    if not os.path.exists(file_path):

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


# ================= ADD NEW DATA TO VECTOR DB =================

def add_new_document_to_db(content):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(content)

    docs = [Document(page_content=c) for c in chunks]

    vectorstore.add_documents(docs)

    vectorstore.persist()


# ================= MAIN FUNCTION =================

def ask_medical_question(query, previous_symptoms=None):

    history = ""

    if previous_symptoms:
        history = "\n".join(previous_symptoms)

    results = vectorstore.similarity_search_with_score(query, k=3)

    if not results:
        best_score = 999
        context = ""

    else:
        best_score = results[0][1]
        context = "\n\n".join([doc.page_content for doc, _ in results])

    SIMILARITY_THRESHOLD = 0.7


    # 🔎 WEB FALLBACK

    if best_score > SIMILARITY_THRESHOLD:

        web_data = search_trusted_medical_sources(query)

        if web_data:

            context = web_data

            cache_web_data(query, web_data)

            add_new_document_to_db(web_data)


    prompt = f"""
You are a medical assistant AI.

Patient History:
{history}

User Question:
{query}

Medical Context:
{context}

Provide:
- Explanation
- Possible diagnosis
- Recommended action
- Safety warning if needed
"""


    response = llm.invoke(prompt)

    response = clean_response(response)

    risk = classify_risk(history + " " + query)

    return response, risk