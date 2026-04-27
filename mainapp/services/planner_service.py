import json
import logging
from django.conf import settings
from groq import Groq

logger = logging.getLogger(__name__)

class PlannerService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    def generate_balanced_plan(self, user_profile):
        """
        AI yordamida abituriyent uchun balanslangan kunlik reja tuzadi.
        Strategiya: 60% Dars, 20% Dam olish, 20% Shaxsiy hayot.
        """
        if not self.client:
            return self._get_fallback_plan(user_profile.user_role)

        role_context = "Abituriyent (OTMga kirishga tayyorgarlik)" if user_profile.user_role == 'applicant' else "Talaba"
        
        prompt = f"""
        Foydalanuvchi roli: {role_context}
        Foydalanuvchi ismi: {user_profile.user.first_name}
        Maqsadi: {user_profile.target_university if user_profile.user_role == 'applicant' else user_profile.selected_field}

        Vazifa: Ushbu foydalanuvchi uchun 1 kunlik professional va balanslangan reja tuzib ber.
        SHARTLAR:
        1. Faqat dars bo'lmasin. Dam olish, ovqatlanish va shaxsiy vaqtni (xobbi, sport) ham qo'sh.
        2. Strategiya: Pomodoro (50 daqiqa dars, 10 daqiqa tanaffus).
        3. Javobni JSON formatida qaytar. Format:
        {{
            "daily_goal": "Bugungi asosiy maqsad",
            "schedule": [
                {{"time": "08:00 - 09:30", "task": "Vazifa nomi", "type": "study/rest/personal"}},
                ...
            ],
            "advice": "AI Mentor'dan kunlik maslahat"
        }}
        """

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sen professional akademik mentor va psixologsan. Foydalanuvchilarni dars bilan ko'mib tashlamasdan, ularga eng samarali va balanslangan reja tuzib berasan."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            plan = json.loads(completion.choices[0].message.content)
            
            # Initializing tasks for tracking
            tasks = []
            for i, item in enumerate(plan.get('schedule', [])):
                tasks.append({
                    "id": i,
                    "task": item['task'],
                    "time": item['time'],
                    "type": item['type'],
                    "status": "pending"
                })
            plan['tasks'] = tasks
            return plan
        except Exception as e:
            logger.error(f"Plan generation error: {e}")
            return self._get_fallback_plan(user_profile.user_role)

    def _get_fallback_plan(self, role):
        if role == 'applicant':
            return {
                "daily_goal": "Matematika va Ingliz tili bazasini mustahkamlash",
                "schedule": [
                    {"time": "08:00 - 10:00", "task": "Asosiy fan: Matematika darslari", "type": "study"},
                    {"time": "10:00 - 11:00", "task": "Yengil dam olish va nonushta", "type": "rest"},
                    {"time": "11:00 - 13:00", "task": "Ingliz tili: Grammatika va Listening", "type": "study"},
                    {"time": "13:00 - 14:30", "task": "Tushlik va shaxsiy vaqt", "type": "personal"},
                ],
                "advice": "Esingizda bo'lsin, sifat miqdordan muhimroq. Har 50 daqiqada dam oling!"
            }
        return {"error": "Plan generation failed"}
