import os
from django.conf import settings
from groq import Groq
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

def get_llm():
    """Groq LLM modelini qaytaradi"""
    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.3
    )

def get_embeddings():
    """HuggingFace orqali embedding yaratish (Local & Free)"""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

import PyPDF2

def process_document(file_path, user_id):
    """
    Hujjatni tahlil qilib, vektor bazaga joylash (RAG uchun)
    """
    text = ""
    try:
        if str(file_path).lower().endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        logger.error(f"Faylni o'qishda xato: {e}")
        return None

    if not text.strip():
        logger.error("Hujjatdan matn ajratib olinmadi.")
        return None

    # 2. Matnni bo'laklarga bo'lish (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    
    docs = [Document(page_content=t, metadata={"user_id": user_id, "source": os.path.basename(file_path)}) for t in chunks]

    # 3. Vektor bazaga saqlash
    persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db', f'user_{user_id}')
    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        persist_directory=persist_directory
    )
    return vector_db

def query_user_documents(query, user_id):
    """Foydalanuvchi hujjatlaridan javob qidirish"""
    persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db', f'user_{user_id}')
    if not os.path.exists(persist_directory):
        return ""

    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings()
    )
    
    results = vector_db.similarity_search(query, k=3)
    context = "\n---\n".join([doc.page_content for doc in results])
    return context
