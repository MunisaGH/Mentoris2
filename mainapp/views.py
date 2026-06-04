import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from groq import Groq

from django.contrib.auth.models import User
from .decorators import role_required
from .validators.rate_limit import rate_limit
from .validators.file_validator import validate_user_document
from django.core.exceptions import ValidationError as DjangoValidationError
from .services.planner_service import PlannerService
from django.core.mail import send_mail
import django.utils.timezone
from .models import (
    ChatMessage, ChatSession, Notification, UserProfile, 
    Subject, UserProgress, EducationalResource, University, UniversityDepartment, UserDocument,
    Course, SubjectCourse, LMSUnit, LMSTest
)
from .services.ai_service import MentorAIService

logger = logging.getLogger(__name__)

NEW_CHAT_TITLES = {
    "uz": "Yangi suhbat",
    "ru": "\u041d\u043e\u0432\u044b\u0439 \u0447\u0430\u0442",
    "en": "New Chat",
}

LANGUAGE_NAMES = {
    "uz": "O'zbek",
    "ru": "Rus",
    "en": "Ingliz",
}

GENERIC_CHAT_ERROR = {
    "uz": "Kechirasiz, hozir javob qaytarishda muammo yuz berdi. Iltimos, birozdan keyin urinib ko'ring.",
    "ru": "\u0418\u0437\u0432\u0438\u043d\u0438\u0442\u0435, \u0441\u0435\u0439\u0447\u0430\u0441 \u043d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u0432\u0435\u0442\u0438\u0442\u044c. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0447\u0443\u0442\u044c \u043f\u043e\u0437\u0436\u0435.",
    "en": "Sorry, there was a problem generating a response right now. Please try again shortly.",
}

DEMO_ONEID_FULL_NAME = "Munisa Axmadjonova Xakimjon qizi"
DEMO_ONEID_PINFL = "31405920040058"


def get_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_new_chat_title(request):
    return NEW_CHAT_TITLES.get(request.LANGUAGE_CODE or "uz", NEW_CHAT_TITLES["en"])


def get_groq_client():
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return None
    return Groq(api_key=api_key)


def get_localized_text(request, mapping):
    return mapping.get(request.LANGUAGE_CODE or "uz", mapping["en"])


def normalize_skills(skills):
    if isinstance(skills, list):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    if isinstance(skills, dict):
        cleaned_skills = []
        for key, value in skills.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if key_text and value_text:
                cleaned_skills.append(f"{key_text}: {value_text}")
            elif key_text:
                cleaned_skills.append(key_text)
        return cleaned_skills
    if isinstance(skills, str) and skills.strip():
        return [item.strip() for item in skills.split(",") if item.strip()]
    return []


def format_skills(skills):
    # This is kept for now if needed elsewhere, but AI logic is moved
    normalized_skills = normalize_skills(skills)
    return ", ".join(normalized_skills) if normalized_skills else "Hali o'rganilmoqda"


@login_required
@role_required(allowed_roles=['applicant', 'student'])
@rate_limit(key_prefix="chat", limit=10, period=60) # 1 daqiqada 10 ta xabar
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Faqat POST so'rovi qo'llab-quvvatlanadi."}, status=405)

    try:
        data = json.loads(request.body or "{}")
        message_content = (data.get("message") or "").strip()
        session_id = data.get("session_id")

        if not message_content:
            return JsonResponse({"answer": "Xabar bo'sh bo'lmasligi kerak."}, status=400)

        if session_id:
            chat_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            chat_session = ChatSession.objects.filter(user=request.user).order_by("-updated_at").first()
            if not chat_session:
                chat_session = ChatSession.objects.create(
                    user=request.user,
                    title=get_new_chat_title(request),
                )

        client = get_groq_client()
        if client is None:
            return JsonResponse(
                {"answer": "GROQ_API_KEY topilmadi. Iltimos, .env faylini tekshiring."},
                status=503,
            )

        ChatMessage.objects.create(session=chat_session, role="user", content=message_content)

        # USE NEW AI SERVICE
        ai_service = MentorAIService(request.user, language_code=request.LANGUAGE_CODE or "uz")
        answer = ai_service.generate_response(message_content, chat_session)

        ChatMessage.objects.create(session=chat_session, role="assistant", content=answer)
        chat_session.save()

        return JsonResponse({
            "answer": answer,
            "session_id": chat_session.id,
        })
    except json.JSONDecodeError:
        return JsonResponse({"answer": "JSON formati noto'g'ri."}, status=400)
    except Exception as error:
        logger.exception("Failed to process chat request: %s", error)
        return JsonResponse({"answer": "Tizimda kutilmagan xatolik yuz berdi."}, status=500)


def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "daily.html", {"is_guest": True})
    
    profile = get_user_profile(request.user)
    if not profile.role_selected and not request.user.is_superuser:
        return redirect("complete_profile")
        
    if request.user.is_superuser:
        return redirect("admin_dashboard")
        
    if profile.user_role == 'applicant':
        return render(request, "applicant_dashboard.html", {"profile": profile})
    elif profile.user_role == 'student':
        return render(request, "student_dashboard.html", {"profile": profile})
        
    return render(request, "daily.html")


@login_required
def mentor_ai(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by("-updated_at")
    active_session = sessions.first()

    if not active_session:
        active_session = ChatSession.objects.create(
            user=request.user,
            title=get_new_chat_title(request),
        )
        sessions = ChatSession.objects.filter(user=request.user).order_by("-updated_at")

    return render(request, "mentor.html", {
        "sessions": sessions,
        "active_session": active_session,
    })


@login_required
def create_session(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Faqat POST so'rovi qo'llab-quvvatlanadi."},
            status=405,
        )

    session = ChatSession.objects.create(user=request.user, title=get_new_chat_title(request))
    return JsonResponse({"session_id": session.id})


@login_required
def delete_session(request, session_id):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Faqat POST so'rovi qo'llab-quvvatlanadi."},
            status=405,
        )

    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({"success": True})


@login_required
def get_session_messages(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session_messages = session.messages.order_by("timestamp")
    data = [{"role": message.role, "content": message.content} for message in session_messages]
    return JsonResponse({"messages": data})


@login_required
def get_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by("-updated_at")
    active = sessions.first()

    if not active:
        active = ChatSession.objects.create(user=request.user, title=get_new_chat_title(request))
        sessions = ChatSession.objects.filter(user=request.user).order_by("-updated_at")

    data = [
        {
            "id": session.id,
            "title": session.title,
            "updated_at": session.updated_at.strftime("%d.%m %H:%M"),
        }
        for session in sessions
    ]
    return JsonResponse({"sessions": data, "active_id": active.id})


def knowledge_base(request):
    subjects = Subject.objects.all()
    
    if not request.user.is_authenticated:
        return render(request, "knowledge.html", {
            "subjects": subjects,
            "is_guest": True
        })

    # Only applicants track DTM subject progress
    if request.user.profile.user_role == 'applicant':
        for s in subjects:
            UserProgress.objects.get_or_create(user=request.user, subject=s)
    
    progress = UserProgress.objects.filter(user=request.user)
    user_documents = UserDocument.objects.filter(user=request.user).order_by("-created_at")
    
    return render(request, "knowledge.html", {
        "subjects": subjects,
        "progress": progress,
        "user_documents": user_documents
    })


def career_hub(request):
    return render(request, "career.html", {"is_guest": not request.user.is_authenticated})


def gov_services(request):
    return render(request, "gov.html", {"is_guest": not request.user.is_authenticated})


@login_required
def complete_profile(request):
    profile = get_user_profile(request.user)

    if request.method == "POST":
        # Handle role selection or profile completion
        role = request.POST.get("user_role")
        if role and not profile.role_selected:
            profile.user_role = role
            profile.role_selected = True
            profile.save()
            
            # If it's a role update from the selection screen, we might stay to fill other fields or redirect
            if "first_name" not in request.POST:
                return redirect("complete_profile")

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        birth_date = request.POST.get("birth_date")

        if first_name and last_name:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            profile.phone_number = phone
            profile.birth_date = birth_date or None
            profile.save()

            Notification.objects.create(
                user=request.user,
                title="Profil yakunlandi",
                message="Sizning profilingiz muvaffaqiyatli to'ldirildi. Endi barcha imkoniyatlardan foydalanishingiz mumkin.",
                link="/profile/",
            )

            return redirect("dashboard")

    return render(request, "complete_profile.html", {"profile": profile})


@login_required
def profile_settings(request):
    profile = get_user_profile(request.user)
    all_subjects = Subject.objects.all()

    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", request.user.first_name)
        request.user.last_name = request.POST.get("last_name", request.user.last_name)
        request.user.save()

        # XAVFSIZLIK: Agar rol allaqachon tanlangan bo'lsa, uni o'zgartirishga yo'l qo'ymaslik
        if not profile.role_selected:
             profile.user_role = request.POST.get("user_role", profile.user_role)
             profile.role_selected = True

        profile.current_score = request.POST.get("current_score", profile.current_score) or 0.0
        profile.target_university = request.POST.get("target_university", profile.target_university)
        profile.selected_field = request.POST.get("selected_field", profile.selected_field)
        
        # New subject tracking
        profile.major_subject_1 = request.POST.get("major_subject_1", profile.major_subject_1)
        profile.major_subject_2 = request.POST.get("major_subject_2", profile.major_subject_2)
        
        profile.phone_number = request.POST.get("phone", profile.phone_number)
        profile.birth_date = request.POST.get("birth_date", profile.birth_date) or None
        profile.university = request.POST.get("university", profile.university)
        profile.faculty = request.POST.get("faculty", profile.faculty)
        profile.major = request.POST.get("major", profile.major)
        profile.graduation_year = request.POST.get("graduation_year") or None
        profile.interests = request.POST.get("interests", profile.interests)
        profile.short_term_goals = request.POST.get("short_term_goals", profile.short_term_goals)
        profile.long_term_goals = request.POST.get("long_term_goals", profile.long_term_goals)

        skills_raw = request.POST.get("skills", "")
        if skills_raw:
            profile.skills_json = normalize_skills(skills_raw)
        else:
            profile.skills_json = []

        profile.save()

        Notification.objects.create(
            user=request.user,
            title="Sozlamalar yangilandi",
            message="Sizning profilingiz ma'lumotlari muvaffaqiyatli saqlandi.",
            link="/profile/",
        )

        messages.success(request, "Ma'lumotlar muvaffaqiyatli saqlandi!")
        return redirect("profile_settings")

    return render(request, "profile.html", {
        "profile": profile,
        "all_subjects": all_subjects,
        "skills_value": ", ".join(normalize_skills(profile.skills_json)),
    })


@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")[:10]
    data = []
    for notification in notifications:
        data.append({
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "link": notification.link or "#",
            "is_read": notification.is_read,
            "created_at": notification.created_at.strftime("%d.%m %H:%M"),
        })
    return JsonResponse({"notifications": data})


@login_required
def mark_all_notifications_read(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Faqat POST so'rovi qo'llab-quvvatlanadi."},
            status=405,
        )

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})


@login_required
def sync_oneid_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Faqat POST so'rovi qo'llab-quvvatlanadi."},
            status=405,
        )

    profile = get_user_profile(request.user)
    official_name = DEMO_ONEID_FULL_NAME
    official_pinfl = DEMO_ONEID_PINFL

    profile.verified_full_name = official_name
    profile.verified_pinfl = official_pinfl
    profile.is_verified_oneid = True
    profile.save()

    request.user.first_name = "Munisa"
    request.user.last_name = "Axmadjonova"
    request.user.save()

    Notification.objects.create(
        user=request.user,
        title="Sinxronizatsiya yakunlandi",
        message=f"OneID ma'lumotlaringiz ({official_name}) muvaffaqiyatli sinxronizatsiya qilindi va profil yangilandi.",
        link="/gov/",
    )

    return JsonResponse({
        "success": True,
        "full_name": official_name,
        "pinfl": official_pinfl,
        "demo_mode": True,
    })


@login_required
@role_required(allowed_roles=['applicant', 'student'])
def university_search(request):
    query = request.GET.get('q', '')
    if query:
        departments = UniversityDepartment.objects.filter(name__icontains=query) | \
                      UniversityDepartment.objects.filter(university__name__icontains=query)
    else:
        departments = UniversityDepartment.objects.all()[:10]
    
    data = []
    for d in departments:
        data.append({
            "id": d.id,
            "uni_name": d.university.name,
            "dept_name": d.name,
            "grant_score": float(d.grant_score),
            "contract_score": float(d.contract_score),
            "quota_grant": d.grant_quota,
            "quota_contract": d.contract_quota
        })
    return JsonResponse({"results": data})

from .utils_ai import process_document

@login_required
@role_required(allowed_roles=['applicant', 'student'])
@rate_limit(key_prefix="upload", limit=3, period=60) # 1 daqiqada 3 ta fayl
def upload_document(request):
    if request.method == "POST" and request.FILES.get('file'):
        file = request.FILES['file']
        
        try:
            # Career AI style deep validation
            validate_user_document(file)
            
            doc = UserDocument.objects.create(
                user=request.user,
                file=file,
                title=file.name,
                status='uploaded'
            )
            
            # Process the document for RAG
            doc.status = 'processing'
            doc.save()
            
            vector_db = process_document(doc.file.path, request.user.id)
            
            if vector_db:
                doc.status = 'indexed'
                doc.save()
                return JsonResponse({
                    "success": True, 
                    "message": "Foydali hujjat yuklandi va RAG tizimiga joylandi.",
                    "doc_id": doc.id
                })
            else:
                doc.status = 'error'
                doc.save()
                return JsonResponse({"success": False, "error": "Hujjatdan matn ajratib olinmadi yoki xatolik."}, status=400)
                
        except DjangoValidationError as e:
            return JsonResponse({"success": False, "error": str(e.message)}, status=400)
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return JsonResponse({"success": False, "error": "Faylni yuklashda xatolik yuz berdi."}, status=500)
            
    return JsonResponse({"success": False, "error": "Faqat POST so'rovi va fayl yuborilishi kerak."}, status=400)

@login_required
def mark_notification_read(request, notification_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


from .services.quiz_service import AIQuizService

@login_required
@role_required(allowed_roles=['applicant', 'student'])
def ai_quiz_view(request):
    subjects = Subject.objects.all()
    return render(request, "ai_quiz.html", {"subjects": subjects})

@login_required
@role_required(allowed_roles=['applicant', 'student'])
def generate_quiz_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Faqat POST so'rovi qabul qilinadi."}, status=405)
    
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '')
        difficulty = data.get('difficulty', 'medium')
        
        if not topic:
            return JsonResponse({"success": False, "error": "Mavzu kiritilishi shart."})
            
        service = AIQuizService(language_code=request.LANGUAGE_CODE or "uz")
        quiz_data = service.generate_quiz(topic=topic, difficulty=difficulty, num_questions=5)
        
        if "error" in quiz_data:
            return JsonResponse({"success": False, "error": quiz_data["error"]})
            
        return JsonResponse({"success": True, "quiz": quiz_data})
    except Exception as e:
        logger.error(f"Generate quiz api error: {e}")
        return JsonResponse({"success": False, "error": "Tizim xatosi."}, status=500)

@login_required
@role_required(allowed_roles=['applicant', 'student'])
def submit_ai_quiz_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Faqat POST so'rovi qabul qilinadi."}, status=405)
        
    try:
        data = json.loads(request.body)
        score_percent = data.get('score', 0)
        topic = data.get('topic', 'Noma\'lum mavzu')
        
        profile = get_user_profile(request.user)
        profile.energy_score = min(100, profile.energy_score + 10) # Test yechgani uchun energiya qo'shiladi
        profile.save()
        
        Notification.objects.create(
            user=request.user,
            title="AI Quiz yakunlandi",
            message=f"\"{topic}\" mavzusi bo'yicha test natijangiz: {score_percent}%.",
            link="/ai-quiz/"
        )
        return JsonResponse({"success": True, "message": "Natija saqlandi!"})
    except Exception as e:
        logger.error(f"Submit quiz api error: {e}")
        return JsonResponse({"success": False, "error": "Tizim xatosi."}, status=500)

@login_required
@role_required(allowed_roles=['applicant', 'student'])
def take_test(request, unit_id):
    unit = get_object_or_404(LMSUnit, id=unit_id)
    tests = unit.tests.all()
    return render(request, "take_test.html", {"unit": unit, "tests": tests})

@login_required
@role_required(allowed_roles=['applicant', 'student'])
def submit_test(request, unit_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    unit = get_object_or_404(LMSUnit, id=unit_id)
    tests = unit.tests.all()
    
    correct_count = 0
    total_count = tests.count()
    
    if total_count == 0:
        return JsonResponse({"success": True, "score": 100})

    for test in tests:
        user_answer = request.POST.get(f"test_{test.id}")
        if user_answer == test.correct_answer:
            correct_count += 1
    
    score_percent = (correct_count / total_count) * 100 if total_count > 0 else 100
    
    # Update UserProgress for the subject associated with this course
    subject_course = SubjectCourse.objects.filter(course=unit.course).first()
    if subject_course:
        progress, created = UserProgress.objects.get_or_create(
            user=request.user, 
            subject=subject_course.subject
        )
        if score_percent >= 70:
            progress.knowledge_percentage = min(100, progress.knowledge_percentage + 5.0)
            progress.completed_lessons_count += 1
            progress.save()
            
            Notification.objects.create(
                user=request.user,
                title="Test yakunlandi",
                message=f"{unit.title} bo'yicha natijangiz: {score_percent}%. Bilim darajangiz oshdi!",
                link="/knowledge/"
            )

    return JsonResponse({
        "success": True, 
        "score": score_percent, 
        "correct": correct_count, 
        "total": total_count
    })

@login_required
@role_required(allowed_roles=['applicant', 'student'])
def generate_plan_api(request):
    """
    AI yordamida balanslangan reja tuzadi va emailga yuboradi.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Faqat POST so'rovi qabul qilinadi."}, status=405)
    profile = get_user_profile(request.user)
    planner = PlannerService()
    
    # 0. Oldingi bajarilmagan vazifalarni "Karzinka"ga o'tkazish
    current_plan = profile.daily_plan_json
    if current_plan and 'tasks' in current_plan:
        backlog = profile.task_backlog_json if isinstance(profile.task_backlog_json, list) else []
        for task in current_plan['tasks']:
            if task['status'] == 'pending':
                backlog.append({
                    "task": task['task'],
                    "time": task['time'],
                    "missed_at": str(django.utils.timezone.now().date())
                })
        profile.task_backlog_json = backlog
    
    plan = planner.generate_balanced_plan(profile)
    
    # 1. Profilga rejani saqlash
    profile.daily_plan_json = plan
    profile.save()
    
    # 2. Email yuborish
    try:
        subject = f"Assalomu alaykum, {request.user.first_name}! Bugungi rejangiz tayyor."
        message = f"Bugungi asosiy maqsad: {plan.get('daily_goal', 'Reja')}\n\nJadval:\n"
        for item in plan.get('schedule', []):
            message += f"- {item['time']}: {item['task']} ({item['type']})\n"
        message += f"\nMaslahat: {plan.get('advice', '')}\n\nMentoris AI - Kelajagingizni biz bilan quring!"
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning(f"Email yuborishda xatolik (foydalanuvchi hali ham rejani ko'radi): {e}")

    return JsonResponse({"success": True, "plan": plan})

@login_required
def toggle_task_api(request, task_id):
    """
    Vazifa holatini o'zgartiradi (done/pending).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Faqat POST so'rovi qabul qilinadi."}, status=405)
    profile = get_user_profile(request.user)
    plan = profile.daily_plan_json
    
    if 'tasks' in plan:
        for task in plan['tasks']:
            if task['id'] == task_id:
                task['status'] = 'done' if task['status'] == 'pending' else 'pending'
                
                # Energy score update
                if task['status'] == 'done':
                    profile.energy_score = min(100, profile.energy_score + 5)
                else:
                    profile.energy_score = max(0, profile.energy_score - 5)
                
                break
        
        profile.daily_plan_json = plan
        profile.save()
        return JsonResponse({"success": True, "status": task['status'], "energy": profile.energy_score})
    
    return JsonResponse({"success": False, "error": "Plan not found"})

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Ushbu sahifaga kirish huquqingiz yo'q. Faqat Super Admin kira oladi.")
        return redirect('dashboard')
    
    # Statistics
    total_users = User.objects.count()
    applicants = UserProfile.objects.filter(user_role='applicant').count()
    students = UserProfile.objects.filter(user_role='student').count()
    
    # Data Lists
    from .models import AuditLog
    all_users = UserProfile.objects.select_related('user').all().order_by('-user__date_joined')
    all_docs = UserDocument.objects.select_related('user').all().order_by('-created_at')
    all_chats = ChatSession.objects.select_related('user').all().order_by('-updated_at')
    all_logs = AuditLog.objects.select_related('user').all().order_by('-timestamp')[:100]
    
    return render(request, "admin_dashboard.html", {
        "total_users": total_users,
        "applicants": applicants,
        "students": students,
        "all_users": all_users,
        "all_docs": all_docs,
        "all_chats": all_chats,
        "all_logs": all_logs,
    })
