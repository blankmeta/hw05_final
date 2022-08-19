from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostCacheTest(TestCase):
    def setUp(self):
        self.my_new_post = Post.objects.create(
            text='Sample text',
            author=User.objects.create_user(username='test_user'),
            group=Group.objects.create(
                title='thatsatestgroup',
                slug='somegroup',
                description='Тестовая группа'
            ),
        )

        self.PRIMORDIAL_POSTS_COUNT = Post.objects.count()

    def test_is_on_index_page_after_delete(self):
        """Запись остается на странцие до принудительной очистки кеша"""
        response = self.client.get(
            reverse('posts:main_page'),
        )

        content = response.content

        Post.objects.filter(pk=self.my_new_post.pk).delete()
        response = self.client.get(
            reverse('posts:main_page'),
        )

        self.assertEqual(response.content, content)

        cache.clear()

        response = self.client.get(
            reverse('posts:main_page'),
        )
        self.assertNotEqual(response.content, content)
