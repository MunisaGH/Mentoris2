import os
import logging
import json
from django.conf import settings
from groq import Groq
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class AIService:
    """Base AI Service with shared utilities"""
    @staticmethod
    def get_embeddings():
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    @staticmethod
    def get_groq_client():
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return None
        return Groq(api_key=api_key)

class DocumentService(AIService):
    """Handles RAG (Retrieval Augmented Generation) logic"""
    @staticmethod
    def query_user_documents(query, user_id):
        persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db', f'user_{user_id}')
        if not os.path.exists(persist_directory):
            return ""

        try:
            vector_db = Chroma(
                persist_directory=persist_directory,
                embedding_function=AIService.get_embeddings()
            )
            results = vector_db.similarity_search(query, k=3)
            return "\n---\n".join([doc.page_content for doc in results])
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return ""

class MentorAIService(AIService):
    """Core logic for the Mentoris AI Mentor"""
    
    def __init__(self, user, language_code="uz"):
        self.user = user
        self.language_code = language_code
        self.profile = getattr(user, 'profile', None)
        self.client = self.get_groq_client()

    def generate_response(self, message_content, chat_session):
        if not self.client:
            return "GROQ_API_KEY topilmadi."

        # 1. Get Context (RAG)
        doc_context = DocumentService.query_user_documents(message_content, self.user.id)

        # 2. Build System Prompt
        system_prompt = self._build_system_prompt(doc_context)

        # 3. Build Message History
        llm_messages = [{"role": "system", "content": system_prompt}]
        
        # Add history (last 10 messages)
        history = chat_session.messages.order_by("-timestamp")[:10]
        for msg in reversed(history):
            llm_messages.append({"role": msg.role, "content": msg.content})

        # Add current message
        llm_messages.append({"role": "user", "content": message_content})

        # 4. Call LLM
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=llm_messages,
                temperature=0.4
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return "Kechirasiz, hozir javob berishda xatolik yuz berdi."

    def _build_system_prompt(self, doc_context):
        user_name = self.user.first_name or self.user.username
        role_display = self.profile.get_user_role_display() if self.profile else "Foydalanuvchi"
        
        lang_names = {"uz": "O'zbek", "ru": "Rus", "en": "Ingliz"}
        lang_name = lang_names.get(self.language_code, "O'zbek")

        prompt = (
            f"Siz {user_name} uchun Mentoris platformasidagi professional akademik AI mentorsiz. "
            "LOYIHA MISSYASI: Abituriyentlarni DTM imtihonlariga maksimal darajada tayyorlash va "
            "talabalarni o'z bilimlariga eng mos keluvchi ish joylariga joylashtirish. "
            f"Foydalanuvchi roli: {role_display}. "
            f"QOIDALAR: FAQAT {lang_name} tilida gapiring. "
        )

        if self.profile:
            prompt += (
                f"Soha: {self.profile.selected_field or 'Aniqlanmagan'}. "
                f"Asosiy fanlar: {self.profile.major_subject_1 or 'Tanlanmagan'} va {self.profile.major_subject_2 or 'Tanlanmagan'}. "
                f"Joriy ball: {self.profile.current_score}. Maqsad: {self.profile.target_university or 'OTM tanlash'}. "
            )

        if self.profile and self.profile.user_role == 'applicant':
            prompt += (
                "\nABITURIYENT UCHUN VAZIFALAR:\n"
                "1. DTM imtihonlariga maksimal tayyorlash. Test yechish texnikalari va fan tahlili.\n"
                "2. Progressni saqlashni eslatish.\n"
                "3. Khan Academy va Edu.uz resurslarini tavsiya qilish."
            )
        elif self.profile and self.profile.user_role == 'student':
            prompt += (
                "\nTALABA UCHUN VAZIFALAR:\n"
                "1. Bilimiga mos ish topishda yordam. CV tahlili va bozor talablari.\n"
                "2. Akademik hujjatlar (RAG) asosida maslahat berish."
            )

        if doc_context:
            prompt += f"\n\nKONTEKST (Yuklangan hujjatlardan):\n{doc_context}"

        prompt += "\nHar doim qisqa, aniq va akademik tilda javob bering."
        return prompt
