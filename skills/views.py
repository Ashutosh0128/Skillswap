from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView,
)
from django.urls import reverse_lazy
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from users.models import Profile
from .models import SkillCategory, Skill, SkillOffer, Session, Review
from .forms import (
    SkillOfferForm, SessionBookingForm, ReviewForm,
    SkillCreateForm, SessionUpdateForm,
)


class SkillCategoryListView(ListView):
    model = SkillCategory
    template_name = 'skills/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for cat in context['categories']:
            cat.active_offer_count = SkillOffer.objects.filter(
                skill__category=cat, is_active=True
            ).count()
        return context


class SkillCategoryDetailView(DetailView):
    model = SkillCategory
    template_name = 'skills/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = self.object.skills.all().order_by('name')
        context['active_offers'] = SkillOffer.objects.filter(
            skill__category=self.object, is_active=True
        ).select_related('teacher__user', 'skill').count()
        return context


class SkillListView(ListView):
    model = Skill
    template_name = 'skills/skill_list.html'
    context_object_name = 'skills'
    paginate_by = 12

    def get_queryset(self):
        queryset = Skill.objects.select_related('category').all()
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                models.Q(name__icontains=q) |
                models.Q(description__icontains=q) |
                models.Q(category__name__icontains=q)
            )
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SkillCategory.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        context['selected_difficulty'] = self.request.GET.get('difficulty')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class SkillDetailView(DetailView):
    model = Skill
    template_name = 'skills/skill_detail.html'
    context_object_name = 'skill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offers'] = self.object.offers.filter(
            is_active=True
        ).select_related('teacher__user').order_by('-created_at')[:10]
        context['total_offers'] = self.object.offers.filter(is_active=True).count()
        context['total_sessions'] = self.object.sessions.count()
        return context


class SkillCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Skill
    form_class = SkillCreateForm
    template_name = 'skills/skill_form.html'
    success_url = reverse_lazy('skills:skill_list')

    def form_valid(self, form):
        messages.success(self.request, 'Skill created successfully!')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff


class SkillUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Skill
    form_class = SkillCreateForm
    template_name = 'skills/skill_form.html'
    success_url = reverse_lazy('skills:skill_list')

    def form_valid(self, form):
        messages.success(self.request, 'Skill updated successfully!')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff


class SkillDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Skill
    template_name = 'skills/skill_confirm_delete.html'
    success_url = reverse_lazy('skills:skill_list')

    def form_valid(self, form):
        messages.success(self.request, 'Skill deleted.')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff


class SkillOfferListView(ListView):
    model = SkillOffer
    template_name = 'skills/offer_list.html'
    context_object_name = 'offers'
    paginate_by = 15

    def get_queryset(self):
        queryset = SkillOffer.objects.filter(
            is_active=True
        ).select_related('teacher__user', 'skill__category')

        skill_id = self.request.GET.get('skill')
        if skill_id:
            queryset = queryset.filter(skill_id=skill_id)

        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(skill__category_id=category_id)

        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(hourly_rate__lte=float(max_price))
            except ValueError:
                pass

        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(teacher__location__icontains=location)

        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['hourly_rate', '-hourly_rate', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = Skill.objects.all()
        context['categories'] = SkillCategory.objects.all()
        context['selected_skill'] = self.request.GET.get('skill')
        context['selected_category'] = self.request.GET.get('category')
        context['max_price'] = self.request.GET.get('max_price', '')
        context['location'] = self.request.GET.get('location', '')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        return context


class SkillOfferCreateView(LoginRequiredMixin, CreateView):
    model = SkillOffer
    form_class = SkillOfferForm
    template_name = 'skills/offer_form.html'

    def form_valid(self, form):
        form.instance.teacher = self.request.user.profile
        messages.success(self.request, 'Your skill offer is live!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('skills:offer_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Skill Offer'
        return context


class SkillOfferDetailView(DetailView):
    model = SkillOffer
    template_name = 'skills/offer_detail.html'
    context_object_name = 'offer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher_reviews'] = Review.objects.filter(
            reviewee=self.object.teacher
        ).select_related('reviewer__user').order_by('-created_at')[:5]
        context['teacher_avg_rating'] = self.object.teacher.get_average_rating()

        if self.request.user.is_authenticated:
            user_profile = self.request.user.profile
            has_pending = Session.objects.filter(
                teacher=self.object.teacher,
                learner=user_profile,
                skill=self.object.skill,
                status__in=['pending', 'confirmed']
            ).exists()
            context['can_book'] = (user_profile != self.object.teacher and not has_pending)
            context['has_completed'] = Session.objects.filter(
                teacher=self.object.teacher,
                learner=user_profile,
                status='completed'
            ).exists()
        else:
            context['can_book'] = False
            context['has_completed'] = False
        return context


class SkillOfferUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SkillOffer
    form_class = SkillOfferForm
    template_name = 'skills/offer_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Offer updated successfully!')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().teacher.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Skill Offer'
        return context

    def get_success_url(self):
        return reverse_lazy('skills:offer_detail', kwargs={'pk': self.object.pk})


class SkillOfferDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SkillOffer
    template_name = 'skills/offer_confirm_delete.html'
    success_url = reverse_lazy('skills:offer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Offer deleted.')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().teacher.user


class SessionBookingView(LoginRequiredMixin, CreateView):
    model = Session
    form_class = SessionBookingForm
    template_name = 'skills/session_book.html'

    def dispatch(self, request, *args, **kwargs):
        self.offer = get_object_or_404(SkillOffer, id=self.kwargs['offer_id'], is_active=True)
        if request.user.is_authenticated:
            user_profile = request.user.profile
            if user_profile == self.offer.teacher:
                messages.error(request, 'You cannot book your own offer.')
                return redirect('skills:offer_detail', pk=self.offer.id)
            existing = Session.objects.filter(
                teacher=self.offer.teacher,
                learner=user_profile,
                skill=self.offer.skill,
                status__in=['pending', 'confirmed']
            ).exists()
            if existing:
                messages.warning(request, 'You already have an active session with this teacher for this skill.')
                return redirect('skills:offer_detail', pk=self.offer.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        session_date = form.cleaned_data['scheduled_date']
        session_time = form.cleaned_data['scheduled_time']
        session_dt = timezone.make_aware(
            timezone.datetime.combine(session_date, session_time)
        )
        if session_dt < timezone.now():
            form.add_error('scheduled_date', 'Cannot book a session in the past.')
            return self.form_invalid(form)

        form.instance.teacher = self.offer.teacher
        form.instance.learner = self.request.user.profile
        form.instance.skill = self.offer.skill
        messages.success(self.request, 'Session booked! Waiting for teacher confirmation.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer'] = self.offer
        return context

    def get_success_url(self):
        return reverse_lazy('skills:session_detail', kwargs={'pk': self.object.pk})


class MySessionsView(LoginRequiredMixin, ListView):
    model = Session
    template_name = 'skills/my_sessions.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        profile = self.request.user.profile
        queryset = Session.objects.filter(
            models.Q(teacher=profile) | models.Q(learner=profile)
        ).select_related('teacher__user', 'learner__user', 'skill')

        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-scheduled_date', '-scheduled_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        context['status_filter'] = self.request.GET.get('status', '')
        context['total_sessions'] = Session.objects.filter(
            models.Q(teacher=profile) | models.Q(learner=profile)
        ).count()
        context['upcoming_count'] = Session.objects.filter(
            models.Q(teacher=profile) | models.Q(learner=profile),
            scheduled_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count()
        return context


class SessionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Session
    template_name = 'skills/session_detail.html'
    context_object_name = 'session'

    def test_func(self):
        session = self.get_object()
        return (
            self.request.user == session.teacher.user or
            self.request.user == session.learner.user or
            self.request.user.is_staff
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.object
        try:
            context['review'] = session.review
        except Review.DoesNotExist:
            context['review'] = None

        context['is_teacher'] = self.request.user == session.teacher.user
        context['is_learner'] = self.request.user == session.learner.user

        if (session.status == 'completed' and not context['review'] and
                self.request.user == session.learner.user):
            context['review_form'] = ReviewForm()

        context['total_cost'] = session.get_total_cost()
        return context


class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Session
    form_class = SessionUpdateForm
    template_name = 'skills/session_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        action = self.request.GET.get('action')
        if action == 'confirm':
            initial['status'] = 'confirmed'
        elif action == 'cancel':
            initial['status'] = 'cancelled'
        elif action == 'complete':
            initial['status'] = 'completed'
        return initial

    def form_valid(self, form):
        old_status = Session.objects.get(pk=self.object.pk).status
        response = super().form_valid(form)
        new_status = self.object.status
        if old_status != new_status:
            msgs = {
                'confirmed': 'Session confirmed!',
                'cancelled': 'Session cancelled.',
                'completed': 'Session marked as completed.',
            }
            messages.success(self.request, msgs.get(new_status, 'Session updated.'))
            # Trigger AI summary generation when session completes
            if new_status == 'completed':
                self._generate_ai_summary(self.object)
        return response

    def _generate_ai_summary(self, session):
        """Generate an AI summary for the completed session."""
        try:
            from django.conf import settings
            import anthropic
            if not settings.ANTHROPIC_API_KEY:
                return
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            prompt = (
                f"A skill-sharing session has just been completed on SkillSwap platform.\n"
                f"Teacher: {session.teacher.user.get_full_name() or session.teacher.user.username}\n"
                f"Learner: {session.learner.user.get_full_name() or session.learner.user.username}\n"
                f"Skill: {session.skill.name} ({session.skill.get_difficulty_display()})\n"
                f"Duration: {session.duration} minutes\n"
                f"Session Notes: {session.notes or 'No notes provided'}\n\n"
                "Generate a concise, professional session summary in 3-4 sentences covering: "
                "what was likely covered, key learning outcomes, and a suggested next step for the learner."
            )
            message = client.messages.create(
                model='claude-3-sonnet-20241022',
                max_tokens=300,
                messages=[{'role': 'user', 'content': prompt}]
            )
            session.ai_summary = message.content[0].text
            session.save(update_fields=['ai_summary'])
        except Exception:
            pass  # Non-critical — never crash the session update

    def test_func(self):
        session = self.get_object()
        return (
            self.request.user == session.teacher.user or
            self.request.user == session.learner.user
        )

    def get_success_url(self):
        return reverse_lazy('skills:session_detail', kwargs={'pk': self.object.pk})


class ReviewCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'skills/review_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(Session, id=self.kwargs['session_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.session = self.session
        form.instance.reviewer = self.request.user.profile
        form.instance.reviewee = self.session.teacher
        messages.success(self.request, 'Review submitted — thank you!')
        return super().form_valid(form)

    def test_func(self):
        return (
            self.request.user == self.session.learner.user and
            self.session.status == 'completed' and
            not hasattr(self.session, 'review')
        )

    def get_success_url(self):
        return reverse_lazy('skills:session_detail', kwargs={'pk': self.session.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.session
        return context


class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'skills/review_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Review updated.')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().reviewer.user

    def get_success_url(self):
        return reverse_lazy('skills:session_detail', kwargs={'pk': self.object.session.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.object.session
        context['editing'] = True
        return context


class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'skills/review_confirm_delete.html'

    def form_valid(self, form):
        messages.success(self.request, 'Review deleted.')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().reviewer.user

    def get_success_url(self):
        return reverse_lazy('skills:session_detail', kwargs={'pk': self.object.session.pk})