from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/toggle/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
    path('users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('skills/', views.admin_skills, name='admin_skills'),
    path('transactions/', views.admin_transactions, name='admin_transactions'),
    path('notifications/', views.admin_notifications, name='admin_notifications'),
    path('notifications/send/', views.admin_send_notification, name='admin_send_notification'),
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/toggle/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
    path('users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    
    # Messaging URLs
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:user_id>/', views.conversation, name='conversation'),
]