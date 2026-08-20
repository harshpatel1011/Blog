from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, Post, Comment
from django.db.models import Q, Count
import re
import random
import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.template.loader import render_to_string

def get_current_user(request):
    user_id = request.session.get("user_id")
    if user_id:
        return User.objects.filter(id=user_id).first()


def home(request):
    user = get_current_user(request)

    posts = Post.objects.all().order_by("-created_at")
    
    query = request.GET.get("q")
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(author__icontains=query)
        )
        
    posts = posts[:8]
    
    trending_posts = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')[:3]
    recent_comments = Comment.objects.select_related('post').order_by('-created_at')[:4]
    top_authors = Post.objects.values('author').annotate(post_count=Count('id')).order_by('-post_count')[:4]

    return render(
        request,
        "home.html",
        {
            "user": user,
            "posts": posts,
            "trending_posts": trending_posts,
            "recent_comments": recent_comments,
            "top_authors": top_authors,
        },
    )


def signup(request):
    if get_current_user(request):
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        name = request.POST.get("name")
        mobile = request.POST.get("mobile")

        if not name:
            messages.error(request, "Name is required!")
            return redirect("signup")

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            messages.error(request, "Invalid email format!")
            return redirect("signup")

        if mobile and not re.match(r"^\+?[0-9]{10,15}$", mobile):
            messages.error(request, "Invalid mobile number format. It should contain 10 to 15 digits.")
            return redirect("signup")

        if not re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$", password
        ):
            messages.error(
                request,
                "Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one number, and one special character.",
            )
            return redirect("signup")

        if password != password_confirm:
            messages.error(request, "Passwords do not match!")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("signup")

        new_user = User(username=username, email=email, password=make_password(password), name=name, mobile=mobile)
        new_user.save()

        request.session["user_id"] = new_user.id
        messages.success(request, "Account created successfully!")
        return redirect("home")

    return render(request, "signup.html")


def login(request):
    if get_current_user(request):
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.filter(email=email).first()

        if user:
            if check_password(password, user.password):
                request.session["user_id"] = user.id
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("home")
            else:
                messages.error(request, "Invalid password!")
        else:
            messages.error(request, "Invalid email address!")
            return redirect("login")

    return render(request, "login.html")


def logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect("home")


def post_add(req):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to add a post.")
        return redirect("login")

    if req.method == "POST":
        Post.objects.create(
            title=req.POST["title"],
            content=req.POST["content"],
            author=user.username,
            image=req.FILES.get("image")
        )
        messages.success(req, "Post created successfully!")
        return redirect("home")
    return render(req, "post_add.html")


def post_detail(req, id):
    user = get_current_user(req)
    post = Post.objects.get(id=id)
    comments = post.comments.filter(parent__isnull=True).order_by("-created_at")
    related_posts = Post.objects.exclude(id=id).order_by("-created_at")[:3]
    return render(
        req,
        "post_detail.html",
        {
            "post": post,
            "comments": comments,
            "user": user,
            "related_posts": related_posts,
        },
    )


def post_update(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to update a post.")
        return redirect("login")

    post = Post.objects.get(id=id)
    if post.author != user.username:
        messages.error(req, "You are not authorized to update this post.")
        return redirect("home")

    if req.method == "POST":
        post.title = req.POST["title"]
        post.content = req.POST["content"]
        
        if req.POST.get("image_clear") == "true":
            post.image.delete(save=False)
            post.image = None
            
        if "image" in req.FILES:
            post.image = req.FILES["image"]
            
        post.save()
        messages.success(req, "Post updated successfully!")
        next_url = req.POST.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("post_detail", id=post.id)
    
    next_url = req.GET.get('next', req.META.get('HTTP_REFERER', ''))
    return render(req, "post_update.html", {"post": post, "next_url": next_url})


def post_delete(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to delete a post.")
        return redirect("login")

    post = Post.objects.get(id=id)
    if post.author == user.username:
        post.delete()
        messages.success(req, "Post deleted successfully!")
    else:
        messages.error(req, "You are not authorized to delete this post.")
    return redirect("home")


def post_like(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to like a post.")
        return redirect("login")

    post = Post.objects.get(id=id)
    if user in post.likes.all():
        post.likes.remove(user)
    else:
        post.likes.add(user)

    referer = req.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("post_detail", id=id)


def comment_add(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to add a comment.")
        return redirect("login")

    post = Post.objects.get(id=id)
    if req.method == "POST":
        Comment.objects.create(
            post=post,
            name=user.username,
            text=req.POST["text"],
        )
        messages.success(req, "Comment added successfully!")
    return redirect("post_detail", id=id)


def comment_update(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to update a comment.")
        return redirect("login")

    comment = Comment.objects.get(id=id)
    post = comment.post

    if user.username != comment.name and user.username != post.author:
        messages.error(req, "You are not authorized to update this comment.")
        return redirect("post_detail", id=post.id)

    if req.method == "POST":
        comment.text = req.POST["text"]
        comment.save()
        messages.success(req, "Comment updated successfully!")
        return redirect("post_detail", id=post.id)

    return render(req, "comment_update.html", {"comment": comment, "post": post})


def comment_delete(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to delete a comment.")
        return redirect("login")

    comment = Comment.objects.get(id=id)
    post = comment.post

    if user.username == comment.name or user.username == post.author:
        comment.delete()
        messages.success(req, "Comment deleted successfully!")
    else:
        messages.error(req, "You are not authorized to delete this comment.")

    return redirect("post_detail", id=post.id)


def comment_like(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to like a comment.")
        return redirect("login")

    comment = Comment.objects.get(id=id)
    if user in comment.likes.all():
        comment.likes.remove(user)
    else:
        comment.likes.add(user)

    referer = req.META.get("HTTP_REFERER")
    return redirect(referer) if referer else redirect("post_detail", id=comment.post.id)


def comment_reply(req, id):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to reply to a comment.")
        return redirect("login")

    parent = Comment.objects.get(id=id)
    if req.method == "POST":
        Comment.objects.create(
            post=parent.post,
            name=user.username,
            text=req.POST.get("text", ""),
            parent=parent,
        )
        messages.success(req, "Reply added successfully!")
    referer = req.META.get("HTTP_REFERER")
    return redirect(referer) if referer else redirect("post_detail", id=parent.post.id)


def profile(req):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to view your profile.")
        return redirect("login")

    posts = Post.objects.filter(author=user.username).order_by("-created_at")

    return render(req, "profile.html", {"user": user, "posts": posts})


def profile_update(req):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to update your profile.")
        return redirect("login")

    if req.method == "POST":
        username = req.POST.get("username")
        current_password = req.POST.get("current_password")
        name = req.POST.get("name")
        mobile = req.POST.get("mobile")

        old_username = user.username
        
        if not check_password(current_password, user.password):
            messages.error(req, "Incorrect password!")
            return redirect("profile_update")
            
        if not name:
            messages.error(req, "Name is required!")
            return redirect("profile_update")
            
        if mobile and not re.match(r"^\+?[0-9]{10,15}$", mobile):
            messages.error(req, "Invalid mobile number format. It should contain 10 to 15 digits.")
            return redirect("profile_update")
            
        if old_username != username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(req, "Username already taken!")
                return redirect("profile_update")

            user.username = username
            Post.objects.filter(author=old_username).update(author=username)
            Comment.objects.filter(name=old_username).update(name=username)

        user.name = name
        user.mobile = mobile
        user.save()
        messages.success(req, "Profile updated successfully!")
        return redirect("profile")

    return render(req, "profile_update.html", {"user": user})

def password_change(req):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to change your password.")
        return redirect("login")
        
    if req.method == "POST":
        current_password = req.POST.get("current_password")
        new_password = req.POST.get("new_password")
        confirm_password = req.POST.get("confirm_password")
        
        if not check_password(current_password, user.password):
            messages.error(req, "Current password is incorrect!")
            return redirect("password_change")

        if not re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$", new_password
        ):
            messages.error(
                req,
                "Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one number, and one special character.",
            )
            return redirect("password_change")
            
        if new_password != confirm_password:
            messages.error(req, "Passwords do not match!")
            return redirect("password_change")
            
        if current_password == new_password:
            messages.error(
                req, "New password cannot be the same as the old password!"
            )
            return redirect("password_change")
            
        otp = generate_otp()
        req.session["otp_code"] = otp
        req.session["change_pwd_new"] = new_password
        req.session["otp_action"] = "change"
        
        send_otp_email(user.email, otp)
        messages.success(
            req, "An OTP has been sent to your email to confirm the password change."
        )
        return redirect("verify_otp")
        
    return render(req, "password_change.html", {"user": user})


def account_delete(req):
    user = get_current_user(req)
    if not user:
        messages.error(req, "Please log in to delete your account.")
        return redirect("login")
        
    if req.method == "POST":
        password = req.POST.get("password")
        if not check_password(password, user.password):
            messages.error(req, "Incorrect password. Account deletion failed.")
            return redirect("account_delete")
            
        otp = generate_otp()
        req.session["otp_code"] = otp
        req.session["otp_action"] = "delete"
        
        send_otp_email(user.email, otp)
        messages.success(
            req,
            "An OTP has been sent to your email to confirm the account deletion.",
        )
        return redirect("verify_otp")
        
    return render(req, "account_delete.html", {"user": user})


def static_page(req, slug):
    user = get_current_user(req)
    title = slug.replace("-", " ").title()
    return render(req, "page.html", {"user": user, "title": title})


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    user = User.objects.filter(email=email).first()
    if user:
        username = user.username
    current_year = datetime.datetime.now().year
    
    send_mail(
        "Your Verification Code",
        f"Your OTP is {otp}",
        "noreply@blog.com",
        [email],
        html_message=render_to_string("otp_email.html", {
            "otp": otp,
            "username": username,
            "current_year": current_year
        }),
        fail_silently=False,
    )


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            otp = generate_otp()
            request.session["otp_code"] = otp
            request.session["reset_email"] = email
            request.session["otp_action"] = "forgot"
            send_otp_email(email, otp)
            messages.success(request, "An OTP has been sent to your email.")
            return redirect("verify_otp")
        else:
            messages.error(request, "No user found with this email.")
    return render(request, "forgot_password.html")


def resend_otp(request):
    action = request.session.get("otp_action")
    email = None

    if action == "forgot":
        email = request.session.get("reset_email")
    elif action in ["change", "delete"]:
        user = get_current_user(request)
        if user:
            email = user.email

    if email:
        otp = generate_otp()
        request.session["otp_code"] = otp
        send_otp_email(email, otp)
        messages.success(request, "A new OTP has been sent to your email.")
    else:
        messages.error(request, "Unable to resend OTP. Please try again.")

    return redirect("verify_otp")


def verify_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        if otp == request.session.get("otp_code"):
            action = request.session.get("otp_action")
            if action == "forgot":
                request.session["otp_verified"] = True
                return redirect("reset_password")
            elif action == "change":
                user = get_current_user(request)
                if user:
                    new_password = request.session.get("change_pwd_new")
                    user.password = make_password(new_password)
                    user.save()
                    request.session.flush()
                    messages.success(
                        request, "Password changed successfully! Please log in again."
                    )
                    return redirect("login")
            elif action == "delete":
                user = get_current_user(request)
                if user:
                    user.delete()
                    request.session.flush()
                    messages.success(
                        request,
                        "Your account and all associated data have been deleted successfully.",
                    )
                    return redirect("login")
        else:
            messages.error(request, "Invalid OTP!")
    return render(request, "verify_otp.html")


def reset_password(request):
    if not request.session.get("otp_verified"):
        return redirect("login")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$", new_password
        ):
            messages.error(
                request,
                "Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one number, and one special character.",
            )
            return redirect("reset_password")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect("reset_password")

        email = request.session.get("reset_email")
        user = User.objects.filter(email=email).first()
        if user:
            user.password = make_password(new_password)
            user.save()
            request.session.flush()
            messages.success(request, "Password reset successfully! Please log in.")
            return redirect("login")

    return render(request, "reset_password.html")
