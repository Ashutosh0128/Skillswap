from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import User
from skills.models import Skill, SkillOffer, Session, Review
from users.models import Profile
from .models import Transaction, Notification, Message, SupportTicket, AdminAnalytics
import json

# In admin_dashboard/views.py, update the admin_dashboard function:

@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=week_ago).count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    total_teachers = Profile.objects.filter(Q(role='teacher') | Q(role='both')).count()
    total_learners = Profile.objects.filter(Q(role='learner') | Q(role='both')).count()
    
    # Session Statistics
    total_sessions = Session.objects.count()
    completed_sessions = Session.objects.filter(status='completed').count()
    pending_sessions = Session.objects.filter(status='pending').count()
    cancelled_sessions = Session.objects.filter(status='cancelled').count()
    
    # Revenue Statistics
    total_revenue = Transaction.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    platform_fees = float(total_revenue) * 0.10 if total_revenue else 0
    
    # Popular Skills
    popular_skills = list(Skill.objects.annotate(
        session_count=Count('sessions')
    ).filter(session_count__gt=0).order_by('-session_count')[:5].values('name', 'session_count'))
    
    # User Demographics - FIXED: Use underscore instead of dot for keys
    age_groups = {
        '18_25': 0,
        '26_35': 0,
        '36_50': 0,
        '50_plus': 0,
        'unknown': 0
    }
    
    for profile in Profile.objects.all():
        age = profile.age
        if age:
            if 18 <= age <= 25:
                age_groups['18_25'] += 1
            elif 26 <= age <= 35:
                age_groups['26_35'] += 1
            elif 36 <= age <= 50:
                age_groups['36_50'] += 1
            elif age > 50:
                age_groups['50_plus'] += 1
        else:
            age_groups['unknown'] += 1
    
    # Location Statistics
    locations = {}
    for profile in Profile.objects.exclude(location=''):
        city = profile.location.split(',')[0].strip()
        locations[city] = locations.get(city, 0) + 1
    top_locations = dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Recent Activities
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_sessions = Session.objects.select_related('skill').order_by('-created_at')[:10]
    recent_transactions = Transaction.objects.select_related('user').order_by('-created_at')[:10]
    
    # Chart Data for last 7 days
    last_7_days = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        users_count = User.objects.filter(date_joined__date=date).count()
        sessions_count = Session.objects.filter(created_at__date=date).count()
        revenue = Transaction.objects.filter(
            created_at__date=date,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        last_7_days.append({
            'date': date.strftime('%Y-%m-%d'),
            'users': users_count,
            'sessions': sessions_count,
            'revenue': float(revenue)
        })
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'total_teachers': total_teachers,
        'total_learners': total_learners,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'pending_sessions': pending_sessions,
        'cancelled_sessions': cancelled_sessions,
        'total_revenue': total_revenue,
        'platform_fees': platform_fees,
        'popular_skills': popular_skills,
        'age_groups': age_groups,  # Now using underscore keys
        'top_locations': top_locations,
        'recent_users': recent_users,
        'recent_sessions': recent_sessions,
        'recent_transactions': recent_transactions,
        'last_7_days': last_7_days,
    }
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_users(request):
    """Manage all users"""
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # Filters
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'admin/users.html', context)


@staff_member_required
def admin_user_detail(request, user_id):
    """View specific user details"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user statistics
    teaching_sessions = Session.objects.filter(teacher=user.profile).count()
    learning_sessions = Session.objects.filter(learner=user.profile).count()
    completed_teaching = Session.objects.filter(teacher=user.profile, status='completed').count()
    completed_learning = Session.objects.filter(learner=user.profile, status='completed').count()
    total_earned = Transaction.objects.filter(user=user, transaction_type='credit', status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_spent = Transaction.objects.filter(user=user, transaction_type='debit', status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get user's offers and sessions
    offers = SkillOffer.objects.filter(teacher=user.profile, is_active=True)
    sessions = Session.objects.filter(Q(teacher=user.profile) | Q(learner=user.profile)).order_by('-created_at')[:20]
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:20]
    reviews_received = Review.objects.filter(reviewee=user.profile).select_related('reviewer__user')
    
    context = {
        'view_user': user,
        'teaching_sessions': teaching_sessions,
        'learning_sessions': learning_sessions,
        'completed_teaching': completed_teaching,
        'completed_learning': completed_learning,
        'total_earned': total_earned,
        'total_spent': total_spent,
        'offers': offers,
        'sessions': sessions,
        'transactions': transactions,
        'reviews_received': reviews_received,
    }
    return render(request, 'admin/user_detail.html', context)


@staff_member_required
def admin_user_toggle_status(request, user_id):
    """Activate/Deactivate user"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {status}.")
    return redirect('admin_user_detail', user_id=user_id)


@staff_member_required
def admin_user_delete(request, user_id):
    """Delete user permanently"""
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"User {username} has been deleted permanently.")
    return redirect('admin_users')


@staff_member_required
def admin_skills(request):
    """Manage all skills"""
    skills = Skill.objects.select_related('category').all().order_by('name')
    
    search = request.GET.get('search')
    if search:
        skills = skills.filter(
            Q(name__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    context = {
        'skills': skills,
        'search': search,
    }
    return render(request, 'admin/skills.html', context)


@staff_member_required
def admin_transactions(request):
    """View all transactions"""
    transactions = Transaction.objects.select_related('user').all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    context = {
        'transactions': transactions,
        'status_filter': status_filter,
    }
    return render(request, 'admin/transactions.html', context)


@staff_member_required
def admin_notifications(request):
    """View and manage notifications"""
    notifications = Notification.objects.select_related('user').all().order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'admin/notifications.html', context)


@staff_member_required
def admin_send_notification(request):
    """Send notification to users"""
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        user_type = request.POST.get('user_type')
        
        if user_type == 'all':
            users = User.objects.filter(is_active=True)
        elif user_type == 'teachers':
            users = User.objects.filter(profile__role__in=['teacher', 'both'])
        elif user_type == 'learners':
            users = User.objects.filter(profile__role__in=['learner', 'both'])
        else:
            users = User.objects.filter(id=user_type)
        
        for user in users:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='system'
            )
        
        messages.success(request, f"Notification sent to {users.count()} users.")
        return redirect('admin_notifications')
    
    users = User.objects.filter(is_active=True)
    context = {'users': users}
    return render(request, 'admin/send_notification.html', context)

@login_required
def inbox(request):
    """User inbox"""
    conversations = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).values('sender', 'receiver').distinct()
    
    # Get unique conversation partners
    partners = set()
    for conv in conversations:
        if conv['sender'] != request.user.id:
            partners.add(conv['sender'])
        if conv['receiver'] != request.user.id:
            partners.add(conv['receiver'])
    
    conversation_users = User.objects.filter(id__in=partners)
    
    context = {
        'conversations': conversation_users,
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def conversation(request, user_id):
    """View conversation with specific user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Mark messages as read
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                message=message
            )
            # Create notification
            Notification.objects.create(
                user=other_user,
                title=f"New message from {request.user.username}",
                message=message[:100],
                notification_type='message',
                link=f'/messaging/conversation/{request.user.id}/'
            )
    
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')
    
    context = {
        'other_user': other_user,
        'messages': messages,
    }
    return render(request, 'messaging/conversation.html', context)