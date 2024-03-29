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
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    posts_count = posts.count()

    page_obj = paginate_queryset(request, posts)

    following = False
    if request.user.is_authenticated and Follow.objects.filter(
            user=request.user, author=author):
        following = True

    context = {
        'page_obj': page_obj,
        'author': author,
        'posts_count': posts_count,
        'following': following,
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
        form.save()

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
    posts = Post.objects.filter(
        author__in=Follow.objects.filter(user=request.user).values('author'))

    page_obj = paginate_queryset(request, posts)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect(reverse('posts:profile', kwargs={'username': username}))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect(reverse('posts:profile', kwargs={'username': username}))
