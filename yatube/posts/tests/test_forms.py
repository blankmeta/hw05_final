from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):
    INITIAL_TEXT_VALUE = 'Some text'
    SAMPLE_TEXT_VALUE = 'Some sample text'
    SAMPLE_EDITED_TEXT_VALUE = 'Some new sample text'

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

    def setUp(self):
        self.author = User.objects.create_user(username='author')
        self.user_client = Client()
        self.user_client.force_login(self.author)

        self.non_author = User.objects.create_user(username='non_author')
        self.non_author_client = Client()
        self.non_author_client.force_login(self.non_author)

        self.new_group = Group.objects.create(
            title='New group',
            slug='group1',
            description='Some description',
        )
        self.new_post = Post.objects.create(
            text='Some text',
            author=self.author,
            group=self.new_group,
        )

        self.PRIMORDIAL_POST_COUNT = Post.objects.count()
        self.PRIMORDIAL_COMMENTS_COUNT = self.new_post.comments.count()

    def create_post(self, client: Client, text: str) -> HttpResponse:
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

        form_data = {
            'text': text,
            'group': self.new_group.pk,
            'image': uploaded,
        }

        response = client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        return response

    def edit_first_post(self, client: Client) -> HttpResponse:
        form_data = {
            'text': self.SAMPLE_EDITED_TEXT_VALUE,
            'group': self.new_group.pk,
        }

        response = client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.new_post.pk}),
            data=form_data,
            follow=True
        )

        return response

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        response = self.create_post(
            client=self.user_client,
            text=self.SAMPLE_TEXT_VALUE,
        )

        self.assertRedirects(response, reverse('posts:profile',
                                               args=[self.author.username]))

        self.assertEqual(Post.objects.count(), self.PRIMORDIAL_POST_COUNT + 1)

        self.assertTrue(
            Post.objects.filter(
                text=self.SAMPLE_TEXT_VALUE,
                group=self.new_group,
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        response = self.edit_first_post(self.user_client)

        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.new_post.pk}))

        self.assertEqual(get_object_or_404(Post, pk=self.new_post.pk).text,
                         self.SAMPLE_EDITED_TEXT_VALUE)

    def test_anonim_post_create(self):
        """Неавторизированный пользователь не может создать пост"""
        self.create_post(
            client=self.client,
            text=self.SAMPLE_TEXT_VALUE,
        )
        self.assertEqual(Post.objects.count(), self.PRIMORDIAL_POST_COUNT)

    def test_anonim_post_edit(self):
        """Неавторизированный пользователь не может редактировать пост"""
        self.edit_first_post(self.client)
        self.assertEqual(
            get_object_or_404(Post, pk=self.new_post.pk).text,
            self.INITIAL_TEXT_VALUE
        )

    def test_non_author_post_edit(self):
        """Пользователь не являющийся автором
        не может редактировать чужой пост"""
        self.edit_first_post(self.non_author_client)
        self.assertEqual(
            get_object_or_404(Post, pk=self.new_post.pk).text,
            self.INITIAL_TEXT_VALUE
        )

    def test_is_only_authorized_user_can_comment_post(self):
        """Неавторизированный пользователь не может комментировать запись"""
        form_data = {
            'text': self.SAMPLE_TEXT_VALUE,
        }

        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.new_post.pk}),
            data=form_data,
            follow=True
        )

        self.assertEqual(self.new_post.comments.count(),
                         self.PRIMORDIAL_COMMENTS_COUNT)

    def test_is_authorized_user_can_comment_post(self):
        """Авторизированный пользователь может комментировать запись"""
        form_data = {
            'text': self.SAMPLE_TEXT_VALUE,
        }

        self.user_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.new_post.pk}),
            data=form_data,
            follow=True
        )

        self.assertEqual(self.new_post.comments.count(),
                         self.PRIMORDIAL_COMMENTS_COUNT + 1)
