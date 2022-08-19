from django.views.generic import CreateView
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:main_page')
    template_name = 'users/signup.html'


class PassChange(CreateView):
    form_class = PasswordChangeView
    success_url = reverse_lazy('users:pass_change_done')
    template_name = 'users/password_change_done.html'


class PasswordReset(CreateView):
    form_class = PasswordResetView
    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset_form.html'
