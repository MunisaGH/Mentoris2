import json
import logging
from datetime import date, datetime, timedelta
from django.conf import settings
from django.utils import timezone
from groq import Groq
from openai import OpenAI

from ..models import Task, Schedule, UserProfile

logger = logging.getLogger(__name__)

class PlannerService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY else None
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY) if hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY else None

    def generate_and_save_plan(self, user):
        """
        AI orqali reja tuzadi va bazadagi Task/Schedule modellariga saqlaydi.
        """
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        # 1. Kontekst yig'ish
        role_context = "Abituriyent" if profile.user_role == 'applicant' else "Talaba/Mutaxassis"
        target = profile.target_university if profile.user_role == 'applicant' else profile.selected_field
        skills = ", ".join(profile.skills_json) if profile.skills_json else "Hali kiritilmagan"
        
        # Qarz vazifalar (muddati o'tgan)
        backlog_tasks = Task.objects.filter(user=user, status='todo', deadline__lt=timezone.now())
        backlog_text = ", ".join([t.title for t in backlog_tasks]) if backlog_tasks.exists() else "Yo'q"

        prompt = f"""
        Foydalanuvchi roli: {role_context}
        Foydalanuvchi ismi: {user.first_name or user.username}
        Maqsadi: {target or 'Belgilanmagan'}
        Joriy ko'nikmalari: {skills}
        Bajarilmagan qarz vazifalari (Backlog): {backlog_text}

        Vazifa: Ushbu foydalanuvchi uchun bugunga (1 kunlik) professional va balanslangan reja tuzib ber.
        SHARTLAR:
        1. 60% dars/ish, 20% dam olish, 20% shaxsiy vaqt bo'lsin.
        2. Agar qarz vazifalari (Backlog) bo'lsa, avval shularni tugatishni jadvalga qo'sh.
        3. Jadval (schedule) va aniq qilinadigan ishlar ro'yxatini (tasks) ber.
        4. Javobni FAQAT to'g'ri JSON formatida qaytar. Hech qanday markdown (```json) ishlatma.

        JSON FORMATI:
        {{
            "tasks": [
                {{"title": "Matematikadan 1-mavzu", "priority": "high", "description": "Batafsil tushuntirish"}},
                {{"title": "Ingliz tili lug'at 50ta", "priority": "medium", "description": ""}}
            ],
            "schedule": [
                {{"start_time": "08:00", "end_time": "10:00", "title": "Matematika o'qish", "task_type": "study", "description": "Fokus bilan o'qish"}},
                {{"start_time": "10:00", "end_time": "10:30", "title": "Nonushta va dam", "task_type": "rest", "description": ""}},
                {{"start_time": "10:30", "end_time": "12:00", "title": "Ingliz tili", "task_type": "study", "description": ""}}
            ]
        }}
        """

        try:
            # AI chaqirish (OpenAI birinchi, yo'q bo'lsa Groq)
            plan_json = None
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Yoki gpt-3.5-turbo
                    messages=[
                        {"role": "system", "content": "Sen professional akademik mentorsan. Javob faqat JSON bo'lishi shart."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                plan_json = json.loads(response.choices[0].message.content)
            elif self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sen professional akademik mentorsan. Javob faqat JSON bo'lishi shart."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                plan_json = json.loads(response.choices[0].message.content)
            else:
                raise Exception("AI API klyuchlari topilmadi!")

            # 2. Bazaga yozish
            today = date.today()
            
            # Bugungi eski AI yaratgan jadvallarni o'chiramiz (yangilash uchun)
            Schedule.objects.filter(user=user, date=today).delete()
            
            # Jadvalni saqlash
            for item in plan_json.get('schedule', []):
                Schedule.objects.create(
                    user=user,
                    date=today,
                    start_time=item.get('start_time', '00:00'),
                    end_time=item.get('end_time', '01:00'),
                    title=item.get('title', 'Vazifa'),
                    task_type=item.get('task_type', 'study'),
                    description=item.get('description', '')
                )
            
            # Tasklarni saqlash (hozirgi kun oxirigacha deadline qilib)
            deadline = timezone.make_aware(datetime.combine(today, datetime.max.time()))
            for item in plan_json.get('tasks', []):
                # Faqat yangi tasks yaratamiz
                Task.objects.create(
                    user=user,
                    title=item.get('title', 'Vazifa'),
                    priority=item.get('priority', 'medium'),
                    description=item.get('description', ''),
                    status='todo',
                    deadline=deadline
                )

            return {"success": True, "message": "Reja muvaffaqiyatli tuzildi"}

        except Exception as e:
            logger.error(f"AI Plan Generation Error: {e}")
            return {"success": False, "message": str(e)}
