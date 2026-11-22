from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import PostForm
from .models import Post


def post_list(request):
    posts = Post.objects.filter(
        published_date__lte=timezone.now()
    ).select_related("author").order_by("-published_date")
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, pk):
    now = timezone.now()
    visible_posts = Post.objects.filter(published_date__lte=now)
    if request.user.is_authenticated:
        visible_posts = Post.objects.filter(
            Q(published_date__lte=now) | Q(author=request.user)
        )
    post = get_object_or_404(visible_posts.select_related("author"), pk=pk)
    return render(request, "blog/post_detail.html", {"post": post})


@login_required
@require_http_methods(["GET", "POST"])
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect("post_detail", pk=post.pk)
    else:
        form = PostForm()
    return render(request, "blog/post_edit.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.published_date = post.published_date or timezone.now()
            post.save()
            return redirect("post_detail", pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, "blog/post_edit.html", {"form": form, "post": post})
