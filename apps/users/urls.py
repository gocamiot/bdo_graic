from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    # path('signin/', views.SignInView.as_view(), name="signin"),
    path('2fa/', views.OTPVerificationView.as_view(), name="otp_view"),
    path('resend-otp/', views.resend_otp, name="resend_otp"),
    # path('signup/', views.SignUpView.as_view(), name="signup"),
    path('signout/', views.signout_view, name="signout"),
    # path('password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    # path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(
    #     template_name='authentication/password-change-done.html'
    # ), name="password_change_done"),
    path('password-reset/', views.UserPasswordResetView.as_view(), name="password_reset"),
    path('password-reset-confirm/<uidb64>/<token>/',
        views.UserPasswrodResetConfirmView.as_view(), name="password_reset_confirm"
    ),
    path('password-reset-done/', auth_views.PasswordResetDoneView.as_view(
        template_name='authentication/password-reset-done.html'
    ), name='password_reset_done'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='authentication/password-reset-complete.html'
    ), name='password_reset_complete'),

    path('profile/', views.profile, name='profile'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('update-user-timezone/', views.update_user_timezone, name='update_user_timezone'),
    path('change-password/', views.change_password, name='change_password'),

    path('user-list/', views.user_list, name='user_list'),
    path('delete-user/<int:id>/', views.delete_user, name="delete_user"),
    path('update-user/<int:id>/', views.update_user, name="update_user"),
    # path('user-change-password/<int:id>/', views.user_change_password, name="user_change_password"),

    path('signin/', views.username_view, name="signin"),
    path('password/', views.password_view, name="password_view"),
    path('password-change/', views.change_password_view, name="change_password_view"),

    path('403/', views.noperms_view, name="403"),
]