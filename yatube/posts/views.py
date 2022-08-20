from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

POSTS_LIMIT = settings.POSTS_LIMIT


def paginate_queryset(request, query):
    paginator = Paginator(query, POSTS_LIMIT)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.select_related('group', 'author')

    page_obj = paginate_queryset(request, posts)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')

    page_obj = paginate_queryset(request, posts)

    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('author')
    posts_count = posts.count()

    page_obj = paginate_queryset(request, posts)

    context = {
        'page_obj': page_obj,
        'author': user,
        'posts_count': posts_count,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm()
    current_post = get_object_or_404(Post, pk=post_id)
    posts_count = current_post.author.posts.count()
    comments = current_post.comments.all()

    context = {
        'post': current_post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        model = form.save(commit=False)
        model.author = request.user
        model.save()

        return redirect(reverse('posts:profile',
                                args=[request.user.username]))

    context = {
        'form': form,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    current_post = Post.objects.get(pk=post_id)

    if request.user != current_post.author:
        return redirect(reverse('posts:post_detail',
                                args=[post_id]))

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=current_post)

    if form.is_valid():
        model = form.save()
        model.save()

        return redirect(reverse('posts:post_detail',
                                args=[post_id]))

    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following = [entry.author for entry
                 in Follow.objects.filter(user=request.user)]
    posts = Post.objects.filter(author__in=following)

    page_obj = paginate_queryset(request, posts)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        Follow.objects.get_or_create(
            user=get_object_or_404(User, username=request.user.username),
            author=get_object_or_404(User, username=username)
        )
    return redirect(reverse('posts:profile', kwargs={'username': username}))


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=user).delete()
    return redirect(reverse('posts:profile', kwargs={'username': username}))
