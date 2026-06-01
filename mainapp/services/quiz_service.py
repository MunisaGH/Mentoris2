import json
import logging
from django.conf import settings
from groq import Groq
from django.utils import timezone

logger = logging.getLogger(__name__)

class AIQuizService:
    def __init__(self, language_code="uz"):
        self.language_code = language_code
        self.client = self._get_client()
        self.model_name = "llama-3.3-70b-versatile"

    def _get_client(self):
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return None
        return Groq(api_key=api_key)

    def generate_quiz(self, topic: str, num_questions: int = 5, difficulty: str = "medium") -> dict:
        """
        Groq (LLaMA) yordamida berilgan mavzu bo'yicha test savollarini shakllantiradi.
        Natija aniq JSON formatida qaytariladi.
        """
        if not self.client:
            logger.error("Groq API kaliti topilmadi.")
            return {"error": "AI xizmati hozircha o'chiq."}

        prompt = f"""
        Siz DTM formatida testlar tuzuvchi professional uzbek o'qituvchisisiz.
        Mavzu: "{topic}"
        Qiyinlik darajasi: {difficulty}
        Savollar soni: {num_questions}

        Iltimos, aniq {num_questions} ta savoldan iborat test yarating. Har bir savol 4 ta variantga ega bo'lsin.
        Javobingiz faqatgina va faqatgina qat'iy JSON formatida bo'lishi shart! Hech qanday qo'shimcha matn yozmang.
        
        JSON formati qolipi:
        {{
            "topic": "{topic}",
            "difficulty": "{difficulty}",
            "questions": [
                {{
                    "id": 1,
                    "question": "Savol matni...",
                    "options": {{
                        "A": "Birinchi variant",
                        "B": "Ikkinchi variant",
                        "C": "Uchinchi variant",
                        "D": "To'rtinchi variant"
                    }},
                    "correct_answer": "B",
                    "explanation": "Nima uchun ushbu javob to'g'ri ekanligini qisqacha tushuntirish"
                }}
            ]
        }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a precise JSON generator that outputs valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=0.3, # Past harorat (aniq va faktik ma'lumotlar uchun)
                response_format={"type": "json_object"}
            )
            
            raw_response = chat_completion.choices[0].message.content
            quiz_data = json.loads(raw_response)
            return quiz_data

        except json.JSONDecodeError:
            logger.error("AI JSON qaytarmadi.")
            return {"error": "Sun'iy intellekt xato formatda javob qaytardi."}
        except Exception as e:
            logger.error(f"Quiz generatsiyasida xatolik: {e}")
            return {"error": "Test generatsiyasida kutilmagan xatolik yuz berdi."}
