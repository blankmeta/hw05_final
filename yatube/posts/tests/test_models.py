from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    SAMPLE_GROUP_TITLE = 'Тестовая группа'
    SAMPLE_POST_TEXT = 'Тестовый пост'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title=cls.SAMPLE_GROUP_TITLE,
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.SAMPLE_POST_TEXT,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, self.SAMPLE_GROUP_TITLE)
        self.assertEqual(self.post.text, self.SAMPLE_POST_TEXT)

    def test_models_have_correct_verbose_names(self):
        """Проверяем, что у моделей корректно работают verbose names."""
        self.assertEqual(self.group._meta.get_field('title').verbose_name,
                         'Название')
        self.assertEqual(self.post._meta.get_field('author').verbose_name,
                         'Автор')
