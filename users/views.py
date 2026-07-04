from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView,
    TemplateView,
    FormView
)
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Profile
from .forms import UserRegisterForm, ProfileUpdateForm, UserUpdateForm


# Home View
class HomeView(TemplateView):
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Import here to avoid circular imports
        from skills.models import Skill, SkillOffer, Session
        
        context['total_users'] = Profile.objects.count()
        context['total_skills'] = Skill.objects.count()
        context['total_offers'] = SkillOffer.objects.filter(is_active=True).count()
        context['total_sessions'] = Session.objects.filter(status='completed').count()
        context['recent_offers'] = SkillOffer.objects.filter(
            is_active=True
        ).select_related('teacher__user', 'skill__category').order_by('-created_at')[:6]
        
        return context


# Custom Login View
class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        messages.success(self.request, f'Welcome back, {self.request.user.username}!')
        return reverse_lazy('users:home')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)


# Custom Logout View
class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)
    
    def get_next_page(self):
        return reverse_lazy('users:home')


# User Registration View
class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 
            'Your account has been created successfully! You can now log in.')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in.')
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)


# Profile Detail View
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        
        from skills.models import Session, SkillOffer, Review
        
        context['offers'] = profile.offers.filter(is_active=True)
        context['reviews_received'] = Review.objects.filter(reviewee=profile).order_by('-created_at')[:10]
        context['average_rating'] = profile.get_average_rating()
        context['total_reviews'] = profile.get_total_reviews()
        context['is_owner'] = self.request.user == profile.user
            
        return context


# Profile Update View
class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'users/profile_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'GET':
            context['user_form'] = UserUpdateForm(instance=self.request.user)
        else:
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
        return context
    
    def form_valid(self, form):
        user_form = UserUpdateForm(self.request.POST, instance=self.request.user)
        if user_form.is_valid():
            user_form.save()
        
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)
    
    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user
    
    def get_success_url(self):
        return reverse_lazy('users:profile_detail', kwargs={'pk': self.object.pk})


# User List View
class UserListView(ListView):
    model = Profile
    template_name = 'users/user_list.html'
    context_object_name = 'profiles'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Profile.objects.select_related('user').all().order_by('-user__date_joined')
        
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                models.Q(user__username__icontains=search_query) |
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(bio__icontains=search_query) |
                models.Q(location__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


# Password Change View
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'users/password_change.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:profile_detail', kwargs={'pk': self.request.user.profile.pk})


# Dashboard View
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        
        from skills.models import Session, SkillOffer, Review
        from django.utils import timezone
        
        today = timezone.now().date()
        context['upcoming_sessions'] = Session.objects.filter(
            models.Q(teacher=profile) | models.Q(learner=profile),
            scheduled_date__gte=today,
            status__in=['pending', 'confirmed']
        ).select_related('teacher__user', 'learner__user', 'skill').order_by('scheduled_date', 'scheduled_time')[:5]
        
        context['active_offers'] = profile.offers.filter(is_active=True).select_related('skill')
        context['recent_reviews'] = Review.objects.filter(reviewee=profile).select_related('reviewer__user').order_by('-created_at')[:3]
        context['total_teaching'] = profile.teaching_sessions.count()
        context['total_learning'] = profile.learning_sessions.count()
        context['completed_sessions'] = profile.teaching_sessions.filter(status='completed').count()
        context['average_rating'] = profile.get_average_rating()
        context['total_reviews'] = profile.get_total_reviews()
        
        return context


# Error Handlers
def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)