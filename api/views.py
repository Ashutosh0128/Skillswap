from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count
from django.conf import settings

# Import models from correct apps
from users.models import Profile
from skills.models import SkillCategory, Skill, SkillOffer, Session, Review
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ProfileSerializer, ProfileUpdateSerializer, PasswordChangeSerializer,
    SkillCategorySerializer, SkillSerializer, SkillOfferSerializer,
    SessionSerializer, SessionCreateSerializer, SessionUpdateSerializer,
    ReviewSerializer, ReviewCreateSerializer,
    AISkillMatchSerializer, AILearningPathSerializer,
)


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'profile_id': user.profile.id,
        })


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out successfully.'})


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed successfully.'})


# ─── Users & Profiles ─────────────────────────────────────────────────────────

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user profiles via API.
    """
    queryset = Profile.objects.select_related('user').all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'bio', 'location']
    ordering_fields = ['user__username', 'created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(bio__icontains=search) |
                Q(location__icontains=search)
            )
        return queryset

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        profile = request.user.profile
        if request.method == 'PATCH':
            serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(ProfileSerializer(profile, context={'request': request}).data)
        return Response(ProfileSerializer(profile, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def offers(self, request, pk=None):
        profile = self.get_object()
        offers = SkillOffer.objects.filter(teacher=profile, is_active=True)
        serializer = SkillOfferSerializer(offers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        profile = self.get_object()
        reviews = Review.objects.filter(reviewee=profile).select_related('reviewer__user')
        avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        return Response({
            'reviews': ReviewSerializer(reviews, many=True).data,
            'average_rating': round(avg, 2),
            'total_reviews': reviews.count(),
        })

    @action(detail=True, methods=['get'])
    def teaching_sessions(self, request, pk=None):
        profile = self.get_object()
        sessions = Session.objects.filter(teacher=profile).select_related('learner__user', 'skill')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def learning_sessions(self, request, pk=None):
        profile = self.get_object()
        sessions = Session.objects.filter(learner=profile).select_related('teacher__user', 'skill')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'bio', 'location']
    ordering_fields = ['user__username', 'created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        profile = request.user.profile
        if request.method == 'PATCH':
            serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(ProfileSerializer(profile, context={'request': request}).data)
        return Response(ProfileSerializer(profile, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def offers(self, request, pk=None):
        profile = self.get_object()
        offers = SkillOffer.objects.filter(teacher=profile, is_active=True)
        serializer = SkillOfferSerializer(offers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        profile = self.get_object()
        reviews = Review.objects.filter(reviewee=profile).select_related('reviewer__user')
        avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        return Response({
            'reviews': ReviewSerializer(reviews, many=True).data,
            'average_rating': round(avg, 2),
            'total_reviews': reviews.count(),
        })


# ─── Skills ───────────────────────────────────────────────────────────────────

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = SkillCategory.objects.all()
    serializer_class = SkillCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.select_related('category').all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        difficulty = self.request.query_params.get('difficulty')
        if category:
            qs = qs.filter(category_id=category)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        return Response({
            'total_skills': Skill.objects.count(),
            'by_category': list(Skill.objects.values('category__name').annotate(count=Count('id'))),
            'by_difficulty': list(Skill.objects.values('difficulty').annotate(count=Count('id'))),
        })


# ─── Offers ───────────────────────────────────────────────────────────────────

class SkillOfferViewSet(viewsets.ModelViewSet):
    queryset = SkillOffer.objects.select_related('teacher__user', 'skill__category').all()
    serializer_class = SkillOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['skill__name', 'teacher__user__username', 'description']
    ordering_fields = ['hourly_rate', 'created_at']

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('active_only'):
            qs = qs.filter(is_active=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(skill__category_id=category)
        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                qs = qs.filter(hourly_rate__lte=float(max_price))
            except ValueError:
                pass
        return qs

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.profile)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def book(self, request, pk=None):
        offer = self.get_object()
        data = request.data.copy()
        data['offer_id'] = offer.id
        serializer = SessionCreateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)


# ─── Sessions ─────────────────────────────────────────────────────────────────

class SessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sessions - queryset is defined in get_queryset method
    """
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    # Define a default queryset to satisfy router requirements
    queryset = Session.objects.none()

    def get_queryset(self):
        profile = self.request.user.profile
        return Session.objects.filter(
            Q(teacher=profile) | Q(learner=profile)
        ).select_related('teacher__user', 'learner__user', 'skill')

    def get_serializer_class(self):
        if self.action == 'create':
            return SessionCreateSerializer
        if self.action in ['update', 'partial_update']:
            return SessionUpdateSerializer
        return SessionSerializer

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        from django.utils import timezone
        profile = request.user.profile
        sessions = Session.objects.filter(
            Q(teacher=profile) | Q(learner=profile),
            scheduled_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).order_by('scheduled_date', 'scheduled_time')
        return Response(SessionSerializer(sessions, many=True).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        session = self.get_object()
        if request.user != session.teacher.user:
            return Response({'error': 'Only the teacher can confirm.'}, status=403)
        if session.status != 'pending':
            return Response({'error': 'Only pending sessions can be confirmed.'}, status=400)
        session.status = 'confirmed'
        session.save()
        return Response(SessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        session = self.get_object()
        if request.user != session.teacher.user:
            return Response({'error': 'Only the teacher can complete.'}, status=403)
        if session.status != 'confirmed':
            return Response({'error': 'Only confirmed sessions can be completed.'}, status=400)
        session.status = 'completed'
        session.save()
        return Response(SessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        session = self.get_object()
        if request.user not in [session.teacher.user, session.learner.user]:
            return Response({'error': 'Not your session.'}, status=403)
        if session.status in ['completed', 'cancelled']:
            return Response({'error': f'Cannot cancel a {session.status} session.'}, status=400)
        session.status = 'cancelled'
        session.save()
        return Response(SessionSerializer(session).data)


# ─── Reviews ──────────────────────────────────────────────────────────────────

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('reviewer__user', 'reviewee__user').all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        reviewee_id = self.request.query_params.get('reviewee')
        if reviewee_id:
            qs = qs.filter(reviewee_id=reviewee_id)
        return qs

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def top_rated(self, request):
        profiles = Profile.objects.annotate(
            avg_rating=Avg('received_reviews__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:10]
        return Response(ProfileSerializer(profiles, many=True, context={'request': request}).data)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        profile = request.user.profile
        today = timezone.now().date()

        upcoming = Session.objects.filter(
            Q(teacher=profile) | Q(learner=profile),
            scheduled_date__gte=today,
            status__in=['pending', 'confirmed']
        ).order_by('scheduled_date')[:5]

        avg_rating = Review.objects.filter(
            reviewee=profile
        ).aggregate(Avg('rating'))['rating__avg'] or 0

        return Response({
            'upcoming_sessions': SessionSerializer(upcoming, many=True).data,
            'active_offers': SkillOfferSerializer(
                profile.offers.filter(is_active=True), many=True
            ).data,
            'recent_reviews': ReviewSerializer(
                Review.objects.filter(reviewee=profile).order_by('-created_at')[:3], many=True
            ).data,
            'stats': {
                'total_teaching': profile.teaching_sessions.count(),
                'total_learning': profile.learning_sessions.count(),
                'completed': profile.teaching_sessions.filter(status='completed').count(),
                'average_rating': round(avg_rating, 2),
                'total_reviews': profile.get_total_reviews(),
                'active_offers': profile.get_active_offers_count(),
            },
        })


# ─── Public Stats ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def public_statistics(request):
    top_skills = Skill.objects.annotate(
        offer_count=Count('offers')
    ).filter(offer_count__gt=0).order_by('-offer_count')[:5]

    return Response({
        'total_users': User.objects.count(),
        'total_skills': Skill.objects.count(),
        'total_offers': SkillOffer.objects.filter(is_active=True).count(),
        'total_sessions': Session.objects.count(),
        'completed_sessions': Session.objects.filter(status='completed').count(),
        'total_reviews': Review.objects.count(),
        'top_skills': [{'name': s.name, 'offer_count': s.offer_count} for s in top_skills],
    })


# ─── AI Agents ────────────────────────────────────────────────────────────────

class AISkillMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AISkillMatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        offers_qs = SkillOffer.objects.filter(is_active=True).select_related(
            'teacher__user', 'skill__category'
        )
        if data.get('max_hourly_rate'):
            offers_qs = offers_qs.filter(hourly_rate__lte=data['max_hourly_rate'])

        offers_text = '\n'.join([
            f"- Offer ID {o.id}: {o.skill.name} ({o.skill.get_difficulty_display()}) "
            f"taught by {o.teacher.user.get_full_name() or o.teacher.user.username}, "
            f"₹{o.hourly_rate}/hr, available {o.available_days} {o.available_times}, "
            f"avg rating: {o.get_average_rating()}"
            for o in offers_qs[:50]
        ])

        prompt = (
            f"You are a skill-match agent for SkillSwap.\n\n"
            f"Learner's goals: {data['goals']}\n"
            f"Current skills: {data.get('current_skills') or 'Not specified'}\n"
            f"Preferred schedule: {data.get('preferred_schedule', 'flexible')}\n\n"
            f"Available offers:\n{offers_text or 'No offers available.'}\n\n"
            "Recommend top 3 offers as JSON: [{\"offer_id\": N, \"skill\": \"...\", \"reason\": \"...\"}]"
        )

        try:
            import anthropic
            if not settings.ANTHROPIC_API_KEY:
                return Response({'error': 'AI service not configured.'}, status=503)
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model='claude-3-sonnet-20241022',
                max_tokens=600,
                messages=[{'role': 'user', 'content': prompt}]
            )
            import json
            raw = message.content[0].text
            start = raw.find('[')
            end = raw.rfind(']') + 1
            recommendations = json.loads(raw[start:end]) if start != -1 else []
            return Response({'recommendations': recommendations})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class AILearningPathView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AILearningPathSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        skills_on_platform = list(
            Skill.objects.values('name', 'difficulty', 'category__name').order_by('category__name')
        )
        skills_text = '\n'.join([
            f"- {s['name']} ({s['difficulty']}) in {s['category__name']}"
            for s in skills_on_platform
        ])

        prompt = (
            f"You are a learning path planner for SkillSwap.\n\n"
            f"Learner goal: {data['goal']}\n"
            f"Current level: {data['current_level']}\n\n"
            f"Available skills:\n{skills_text}\n\n"
            "Create a learning path of 4-6 milestones as JSON: "
            '{"path": [{"step": N, "milestone": "...", "skill": "...", "duration_weeks": N, "why": "..."}]}'
        )

        try:
            import anthropic
            if not settings.ANTHROPIC_API_KEY:
                return Response({'error': 'AI service not configured.'}, status=503)
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model='claude-3-sonnet-20241022',
                max_tokens=800,
                messages=[{'role': 'user', 'content': prompt}]
            )
            import json
            raw = message.content[0].text
            start = raw.find('{')
            end = raw.rfind('}') + 1
            path_data = json.loads(raw[start:end]) if start != -1 else {}
            return Response({'learning_path': path_data.get('path', [])})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class AIReviewModerationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        comment = request.data.get('comment', '')
        rating = request.data.get('rating', 3)

        if not comment:
            return Response({'flagged': False, 'reason': ''})

        prompt = (
            f"Moderate this review for SkillSwap:\n"
            f"Rating: {rating}/5\n"
            f"Comment: \"{comment}\"\n\n"
            "Is this spam/abusive/fake? Reply JSON: {\"flagged\": true/false, \"reason\": \"...\"}"
        )

        try:
            import anthropic, json
            if not settings.ANTHROPIC_API_KEY:
                return Response({'flagged': False, 'reason': ''})
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model='claude-3-sonnet-20241022',
                max_tokens=100,
                messages=[{'role': 'user', 'content': prompt}]
            )
            raw = message.content[0].text
            start = raw.find('{')
            end = raw.rfind('}') + 1
            result = json.loads(raw[start:end]) if start != -1 else {'flagged': False, 'reason': ''}
            return Response(result)
        except Exception as e:
            return Response({'flagged': False, 'reason': '', 'error': str(e)})