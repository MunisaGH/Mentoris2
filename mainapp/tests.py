import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ChatMessage, ChatSession, Notification, UserProfile


class UserProfileSignalTests(TestCase):
    def test_user_creation_creates_profile(self):
        user = User.objects.create_user(
            username="signal-user",
            email="signal@example.com",
            password="testpass123",
        )

        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_saving_user_recreates_missing_profile_safely(self):
        user = User.objects.create_user(
            username="recreate-user",
            email="recreate@example.com",
            password="testpass123",
        )
        user.profile.delete()

        user.first_name = "Mentor"
        user.save()

        self.assertTrue(UserProfile.objects.filter(user=user).exists())


class AuthenticatedApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mentor",
            email="mentor@example.com",
            password="testpass123",
        )
        self.client.force_login(self.user)
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.csrf_client.force_login(self.user)

    def test_create_session_returns_session_id(self):
        response = self.client.post(reverse("create_session"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("session_id", response.json())
        self.assertTrue(ChatSession.objects.filter(user=self.user).exists())

    def test_delete_session_removes_owned_session(self):
        session = ChatSession.objects.create(user=self.user, title="Delete me")

        response = self.client.post(reverse("delete_session", args=[session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ChatSession.objects.filter(id=session.id).exists())

    def test_get_session_messages_returns_ordered_messages(self):
        session = ChatSession.objects.create(user=self.user, title="History")
        ChatMessage.objects.create(session=session, role="user", content="First")
        ChatMessage.objects.create(session=session, role="assistant", content="Second")

        response = self.client.get(reverse("get_session_messages", args=[session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["messages"],
            [
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "Second"},
            ],
        )

    def test_mark_notification_read_updates_single_notification(self):
        notification = Notification.objects.create(
            user=self.user,
            title="Read me",
            message="Body",
        )

        response = self.client.post(reverse("mark_notification_read", args=[notification.id]))

        notification.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(notification.is_read)

    def test_mark_all_notifications_read_updates_unread_notifications(self):
        Notification.objects.create(user=self.user, title="One", message="Body")
        Notification.objects.create(user=self.user, title="Two", message="Body")

        response = self.client.post(reverse("mark_all_notifications_read"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_chat_api_rejects_empty_message(self):
        response = self.client.post(
            reverse("chat_api"),
            data=json.dumps({"message": "   "}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["answer"], "Xabar bo'sh bo'lmasligi kerak.")

    def test_chat_api_rejects_invalid_json(self):
        response = self.client.post(
            reverse("chat_api"),
            data="{invalid-json}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["answer"], "JSON formati noto'g'ri.")

    @override_settings(GROQ_API_KEY=None)
    def test_chat_api_returns_503_when_groq_key_missing(self):
        response = self.client.post(
            reverse("chat_api"),
            data=json.dumps({"message": "Salom"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("GROQ_API_KEY", response.json()["answer"])

    def test_sync_oneid_updates_profile(self):
        response = self.client.post(reverse("sync_oneid_api"))

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.profile.is_verified_oneid)
        self.assertTrue(response.json()["demo_mode"])

    def test_chat_api_requires_csrf(self):
        response = self.csrf_client.post(
            reverse("chat_api"),
            data=json.dumps({"message": "Salom"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_sync_oneid_requires_csrf(self):
        response = self.csrf_client.post(reverse("sync_oneid_api"))

        self.assertEqual(response.status_code, 403)
