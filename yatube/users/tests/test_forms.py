from django.contrib.auth import get_user_model

from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        User.objects.create(
            username='user111'
        )

    def test_create_post(self):
        """Валидная форма создает нового пользователя."""
        primordial_users_count = User.objects.count()

        form_data = {
            'first_name': 'Thomas',
            'last_name': 'Anderson',
            'username': 'ThomasAnderson',
            'email': 'ta22@gmail.com',
            'password1': 'SomeSample123',
            'password2': 'SomeSample123'
        }

        self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )

        self.assertEqual(User.objects.count(), primordial_users_count + 1)

        self.assertTrue(
            User.objects.filter(
                username='ThomasAnderson'
            ).exists()
        )
