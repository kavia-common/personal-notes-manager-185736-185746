from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Note


class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')  # Make sure the URL is named
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})


class AuthAndNotesTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user1 = User.objects.create_user(username="alice", password="password123")
        self.user2 = User.objects.create_user(username="bob", password="password123")
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # some notes
        Note.objects.create(title="Alice 1", content="c1", owner=self.user1)
        Note.objects.create(title="Alice 2", content="c2", owner=self.user1, is_archived=True)
        Note.objects.create(title="Bob 1", content="c3", owner=self.user2)

    def auth_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        return client

    def test_auth_required(self):
        # notes list should require auth
        url = "/api/notes/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_token_login(self):
        url = "/api/auth/token/login/"
        resp = self.client.post(url, {"username": "alice", "password": "password123"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.data)

    def test_register(self):
        url = "/api/auth/register/"
        resp = self.client.post(url, {"username": "charlie", "password": "pass1234"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertIn("token", resp.data)

    def test_list_only_own_notes_and_filters(self):
        client = self.auth_client(self.token1.key)
        url = "/api/notes/"
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Should only see 2 notes (belonging to alice)
        self.assertEqual(resp.data["count"], 2)
        # filter archived=false should return 1
        resp2 = client.get(url, {"archived": "false"})
        self.assertEqual(resp2.data["count"], 1)
        # filter archived=true should return 1
        resp3 = client.get(url, {"archived": "true"})
        self.assertEqual(resp3.data["count"], 1)

    def test_create_sets_owner(self):
        client = self.auth_client(self.token1.key)
        resp = client.post("/api/notes/", {"title": "new", "content": "body"}, format="json")
        self.assertEqual(resp.status_code, 201)
        # retrieve via list and ensure present
        resp_list = client.get("/api/notes/")
        titles = [n["title"] for n in resp_list.data["results"]]
        self.assertIn("new", titles)

    def test_permissions_retrieve_update_delete(self):
        # Alice tries to access Bob's note
        bob_note = Note.objects.filter(owner=self.user2).first()
        client_alice = self.auth_client(self.token1.key)
        resp = client_alice.get(f"/api/notes/{bob_note.id}/")
        self.assertEqual(resp.status_code, 404)  # not in queryset

        # Bob can update his note
        client_bob = self.auth_client(self.token2.key)
        resp2 = client_bob.patch(f"/api/notes/{bob_note.id}/", {"title": "updated"}, format="json")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data["title"], "updated")

        # Bob delete
        resp3 = client_bob.delete(f"/api/notes/{bob_note.id}/")
        self.assertEqual(resp3.status_code, 204)

    def test_archive_actions(self):
        client = self.auth_client(self.token1.key)
        note = Note.objects.filter(owner=self.user1, is_archived=False).first()
        resp = client.post(f"/api/notes/{note.id}/archive/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["is_archived"])

        resp2 = client.post(f"/api/notes/{note.id}/unarchive/")
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.data["is_archived"])

    def test_token_logout(self):
        client = self.auth_client(self.token1.key)
        resp = client.post("/api/auth/token/logout/")
        self.assertIn(resp.status_code, (200, 204))  # we return 204
        # Subsequent authorized call should fail since token deleted
        resp2 = client.get("/api/notes/")
        self.assertEqual(resp2.status_code, 401)
