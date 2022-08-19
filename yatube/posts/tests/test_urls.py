from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        author = User.objects.create_user(username='post_author')
        cls.new_group = Group.objects.create(
            title='Группа 1',
            slug='test_group',
            description='Тестовая группа'
        )
        cls.new_post = Post.objects.create(
            text='Sample test',
            author=author,
            group=get_object_or_404(Group, slug='test_group')
        )

    def setUp(self):
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author = get_object_or_404(User, username='post_author')
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_exist_at_desired_location(self):
        """Проверка доступности страниц любому пользователю."""
        urls = ['/',
                f'/group/{self.new_group.slug}/',
                f'/profile/{self.user.username}/',
                f'/posts/{self.new_post.pk}/']

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Несуществующая страница возвращает 404."""
        response = self.client.get('unexisting_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            '/': 'posts/index.html',
            f'/group/{self.new_group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.new_post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.new_post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }

        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_post_url_redirect_anonymous_to_login_page(self):
        """Страница /posts/1/edit/ перенаправит анонимного пользователя
        на страницу логина."""
        response = self.client.get(f'/posts/{self.new_post.pk}/edit/',
                                   follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.new_post.pk}/edit/'
        )

    def test_create_url_redirect_anonymous_to_login_page(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина."""
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_post_url_redirect_non_author_to_post_page(self):
        """Страница /posts/1/edit/ перенаправит авторизированного пользователя
        на страницу поста."""
        response = self.authorized_client.get(
            f'/posts/{self.new_post.pk}/edit/', follow=True)
        self.assertRedirects(response, f'/posts/{self.new_post.pk}/')
