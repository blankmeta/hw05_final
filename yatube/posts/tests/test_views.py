from typing import Dict

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostsPagesTests(TestCase):
    POSTS_COUNT_WITH_FIRST_AUTHOR = 12
    POSTS_COUNT_WITH_GROUP = 11
    POSTS_COUNT_WITHOUT_GROUP = 2
    GENERAL_POSTS_COUNT = 13
    SAMPLE_GROUP_SLUG = 'test_group'
    SAMPLE_FIRST_AUTHOR_NAME = 'post_author'
    SAMPLE_POST_ID = 1
    POSTS_LIMIT = 10

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_author = User.objects.create_user(
            username=cls.SAMPLE_FIRST_AUTHOR_NAME)
        second_author = User.objects.create_user(username='somebody')
        new_group = Group.objects.create(
            title='Группа 1',
            slug=cls.SAMPLE_GROUP_SLUG,
            description='Тестовая группа'
        )
        for i in range(cls.GENERAL_POSTS_COUNT - 1):
            Post.objects.create(
                text='Sample test',
                author=cls.first_author
                if i < cls.POSTS_COUNT_WITH_FIRST_AUTHOR
                else second_author,
                group=new_group if i < cls.POSTS_COUNT_WITH_GROUP else None
            )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.first_author)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        self.my_new_post = Post.objects.create(
            text='Without further interruption',
            author=User.objects.create_user(username='test_user'),
            group=Group.objects.create(
                title='thatsatestgroup',
                slug='somegroup',
                description='Тестовая группа'
            ),
            image=uploaded
        )

    def check_context(self, reversed_url: reverse, expected: Dict):
        response = self.author_client.get(reversed_url)
        context = response.context

        for name in expected:
            with self.subTest(name=name):
                self.assertIsInstance(context[name], expected[name])

    def image_in_page_obj_context(self, reversed_url: reverse):
        """В объекте паджинатора в context передается изображение"""
        response = self.author_client.get(reversed_url)
        context = response.context
        self.assertIsInstance(context['page_obj'].object_list[0].image,
                              ImageFieldFile)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_templates = {
            reverse(
                'posts:group_list', kwargs={'slug': self.SAMPLE_GROUP_SLUG}
            ):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.SAMPLE_FIRST_AUTHOR_NAME}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.SAMPLE_POST_ID}):
                'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.SAMPLE_POST_ID}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            'doesnt_exist': 'core/404.html'
        }

        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Context включает в себя объект Page."""
        response = self.author_client.get(reverse('posts:main_page'))
        context = response.context.get('page_obj')
        self.assertIsInstance(context, Page)

    def test_group_posts_context(self):
        """Context group_posts включает в себя объекты необходимых классов."""
        expected = {
            'group': Group,
            'page_obj': Page,
        }

        self.check_context(
            reverse('posts:group_list',
                    kwargs={'slug': self.SAMPLE_GROUP_SLUG}),
            expected)

    def test_profile_posts_context(self):
        """Context profile включает в себя объекты необходимых классов."""
        expected = {
            'page_obj': Page,
            'author': User,
            'posts_count': int,
        }

        self.check_context(
            reverse('posts:profile',
                    kwargs={'username': self.SAMPLE_FIRST_AUTHOR_NAME}
                    ),
            expected)

    def test_profile_posts_count_is_1(self):
        """Количество постов в контексте profile
         соответствует реальному количеству."""
        response = self.author_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.SAMPLE_FIRST_AUTHOR_NAME}))
        context = response.context.get('posts_count')
        self.assertEqual(context, self.POSTS_COUNT_WITH_FIRST_AUTHOR)

    def test_post_detail_posts_context(self):
        """Context post_detail включает в себя объекты необходимых классов."""
        expected = {
            'post': Post,
            'posts_count': int,
        }

        self.check_context(reverse('posts:post_detail',
                                   kwargs={'post_id': self.SAMPLE_POST_ID}),
                           expected)

    def test_post_detail_posts_count_is_1(self):
        """Количество постов в контексте post_detail
         соответствует реальному количеству."""
        response = self.author_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.SAMPLE_POST_ID}))
        context = response.context.get('posts_count')
        self.assertEqual(context, self.POSTS_COUNT_WITH_FIRST_AUTHOR)

    def test_first_main_page_contains_ten_records(self):
        """Количество постов на первой странице всех записей равно 10."""
        response = self.client.get(reverse('posts:main_page'))
        self.assertEqual(len(response.context['page_obj']),
                         self.POSTS_LIMIT)

    def test_second_main_page_contains_three_records(self):
        """Количество постов на первой странице всех записей равно 3."""
        response = self.client.get(reverse('posts:main_page') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.GENERAL_POSTS_COUNT - self.POSTS_LIMIT)

    def test_first_group_page_contains_ten_records(self):
        """Количество постов на первой странице записей группы равно 10."""
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.SAMPLE_GROUP_SLUG}))
        self.assertEqual(len(response.context['page_obj']),
                         self.POSTS_LIMIT)

    def test_second_group_page_contains_one_record(self):
        """Количество постов на первой странице записей группы равно 1."""
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.SAMPLE_GROUP_SLUG}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POSTS_COUNT_WITH_GROUP - self.POSTS_LIMIT)

    def test_first_profile_page_contains_ten_records(self):
        """Количество постов на первой странице
        записей пользователя равно 10."""
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': self.SAMPLE_FIRST_AUTHOR_NAME})
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.POSTS_LIMIT)

    def test_second_profile_page_contains_two_records(self):
        """Количество постов на первой странице записей группы равно 1."""
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': self.SAMPLE_FIRST_AUTHOR_NAME}) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_COUNT_WITH_FIRST_AUTHOR - self.POSTS_LIMIT)

    def test_is_post_on_main_page(self):
        response = self.client.get(reverse('posts:main_page'))
        posts_on_page = response.context.get('page_obj').object_list
        self.assertIn(self.my_new_post, posts_on_page)

    def test_is_post_on_group_page(self):
        response = self.client.get((
            reverse('posts:group_list',
                    kwargs={'slug': self.my_new_post.group.slug})))
        posts_on_page = response.context.get('page_obj').object_list
        self.assertIn(self.my_new_post, posts_on_page)

    def test_is_post_on_profile_page(self):
        response = self.client.get((
            reverse('posts:profile',
                    kwargs={'username': self.my_new_post.author.username})))
        posts_on_page = response.context.get('page_obj').object_list
        self.assertIn(self.my_new_post, posts_on_page)

    def test_is_not_post_on_another_group_page(self):
        response = self.client.get((
            reverse('posts:group_list',
                    kwargs={'slug': self.SAMPLE_GROUP_SLUG})))
        posts_on_page = response.context.get('page_obj').object_list
        self.assertNotIn(self.my_new_post, posts_on_page)

    def test_is_image_in_index_context(self):
        """В объекте паджинатора в context index передается изображение"""
        self.image_in_page_obj_context(reverse('posts:main_page'))

    def test_is_image_in_profile_context(self):
        """В объекте паджинатора в context profile передается изображение"""
        self.image_in_page_obj_context(
            reverse('posts:profile',
                    kwargs={'username': self.SAMPLE_FIRST_AUTHOR_NAME}
                    )
        )

    def test_is_image_in_group_page_context(self):
        """В объекте паджинатора в context group_page передается изображение"""
        self.image_in_page_obj_context(
            reverse('posts:group_list',
                    kwargs={
                        'slug': self.SAMPLE_GROUP_SLUG}))

    def test_is_image_in_post_detail_context(self):
        response = self.author_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.my_new_post.pk}))
        context = response.context
        self.assertIsInstance(context['post'].image, ImageFieldFile)
