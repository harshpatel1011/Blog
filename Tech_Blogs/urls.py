from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('post/add/', views.post_add, name='post_add'),
    path('post/<int:id>/', views.post_detail, name='post_detail'),
    path('post/<int:id>/update/', views.post_update, name='post_update'),
    path('post/<int:id>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:id>/like/', views.post_like, name='post_like'),
    path('post/<int:id>/comment/', views.comment_add, name='comment_add'),
    path('comment/<int:id>/update/', views.comment_update, name='comment_update'),
    path('comment/<int:id>/delete/', views.comment_delete, name='comment_delete'),
    path('comment/<int:id>/like/', views.comment_like, name='comment_like'),
    path('comment/<int:id>/reply/', views.comment_reply, name='comment_reply'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/password/', views.password_change, name='password_change'),
    path('profile/delete/', views.account_delete, name='account_delete'),
    path('page/<str:slug>/', views.static_page, name='static_page'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
