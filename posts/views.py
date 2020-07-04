from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from yatube.settings import TEMPLATE_CACHE_TIMEOUTS
from .models import Post, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


def index(request):
    posts = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(
        request, 'index.html',
        {
            'page': page,
            'paginator': paginator,
            'cache_timeout': TEMPLATE_CACHE_TIMEOUTS['index']
        })


def group_posts(request, slug):
    posts = Post.objects.select_related('author', 'group').filter(
        group__slug=slug)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    if posts:
        group = posts[0].group
        return render(request, 'group.html',
                      {'group': group, 'page': page, 'paginator': paginator})
    else:
        return HttpResponseNotFound(request)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    try:
        following = Follow.objects.get(author=author.pk, user=request.user.pk)
    except Follow.DoesNotExist:
        following = None
    posts = author.posts.select_related('author', 'group').all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(request, 'profile.html',
                  {'author': author, 'posts': posts,
                   'page': page, 'paginator': paginator,
                   'following': following})


def post_view(request, username: str, post_id: int):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        author__username=username, pk=post_id)

    comment_form = CommentForm()

    author = post.author
    comments = post.comments.all()
    post_count = author.posts.count()

    return render(request, 'post.html',
                  {
                      'author': author, 'post': post,
                      'post_count': post_count,
                      'comments': comments,
                      'form': comment_form,
                  })


@login_required
def post_new(request):
    form = PostForm(request.POST, request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        redirect_to = reverse('index')
        return redirect(redirect_to)
    else:
        return render(
            request, 'post_edit.html', context={
                'form': form,
                'create_or_edit': True
            })


@login_required
def post_edit(request, username, post_id):
    if username != request.user.username:
        redirect(
            reverse('post', kwargs=dict(username=username, post_id=post_id)))
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save(commit=True)
            return redirect(
                reverse('post',
                        kwargs=dict(username=username, post_id=post_id)))
    return render(
        request, 'post_edit.html', context={
            'form': form,
            'create_or_edit': False,
            'post': post
        })


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username: str, post_id: int):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    url_kwargs = {'username': username, 'post_id': post_id}
    redirect_to = reverse('post', kwargs=url_kwargs)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect(redirect_to)


@login_required
def follow_index(request):
    following_posts = Post.objects.select_related('author').filter(
        author__following__user=request.user)
    paginator = Paginator(following_posts, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(
        request, 'follow.html',
        {
            'page': page,
            'paginator': paginator,
            'cache_timeout': TEMPLATE_CACHE_TIMEOUTS['index'],
        }
    )


@login_required
def profile_follow(request, username):
    if username != request.user.username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
    redirect_to = reverse('follow_index')
    return redirect(redirect_to)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author.pk, user=request.user.pk).delete()
    return redirect(reverse('index'))
