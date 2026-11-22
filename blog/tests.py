from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Post

User = get_user_model()


class BlogAccessTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="test-pass-123")
        self.other_user = User.objects.create_user(username="other", password="test-pass-456")
        self.published = Post.objects.create(
            author=self.author,
            title="Publicación pública",
            text="Contenido visible",
            published_date=timezone.now(),
        )
        self.draft = Post.objects.create(
            author=self.author,
            title="Borrador privado",
            text="Contenido no publicado",
        )

    def test_home_lists_only_published_posts(self):
        response = self.client.get(reverse("post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Publicación pública")
        self.assertNotContains(response, "Borrador privado")

    def test_anonymous_user_cannot_open_draft_detail(self):
        response = self.client.get(reverse("post_detail", args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

    def test_author_can_open_own_draft(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse("post_detail", args=[self.draft.pk]))
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_open_someone_elses_draft(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("post_detail", args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

    def test_create_requires_login(self):
        response = self.client.get(reverse("post_new"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_logged_in_user_can_create_post(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse("post_new"), {
            "title": "Nuevo artículo",
            "text": "Texto del artículo",
        })
        created = Post.objects.get(title="Nuevo artículo")
        self.assertEqual(created.author, self.author)
        self.assertIsNotNone(created.published_date)
        self.assertRedirects(response, reverse("post_detail", args=[created.pk]))

    def test_edit_requires_login(self):
        response = self.client.get(reverse("post_edit", args=[self.published.pk]))
        self.assertEqual(response.status_code, 302)

    def test_only_author_can_edit_post(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("post_edit", args=[self.published.pk]))
        self.assertEqual(response.status_code, 404)

    def test_author_can_edit_post(self):
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("post_edit", args=[self.published.pk]),
            {"title": "Título actualizado", "text": "Texto actualizado"},
        )
        self.published.refresh_from_db()
        self.assertEqual(self.published.title, "Título actualizado")
        self.assertRedirects(response, reverse("post_detail", args=[self.published.pk]))
