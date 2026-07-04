from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SkillViewSet,
    SkillOfferViewSet,
    SessionViewSet,
    UserProfileViewSet,
    CategoryViewSet,
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    ChangePasswordAPIView,
    DashboardAPIView,
    public_statistics,
    AISkillMatchView,
    AILearningPathView,
    AIReviewModerationView,
)

router = DefaultRouter()
router.register(r'skills', SkillViewSet, basename='api-skills')
router.register(r'offers', SkillOfferViewSet, basename='api-offers')
router.register(r'sessions', SessionViewSet, basename='api-sessions')
router.register(r'profiles', UserProfileViewSet, basename='api-profiles')
router.register(r'categories', CategoryViewSet, basename='api-categories')

urlpatterns = [
    # API endpoints (all start with /api/)
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    
    # Auth endpoints
    path('auth/register/', RegisterAPIView.as_view(), name='api_register'),
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('auth/change-password/', ChangePasswordAPIView.as_view(), name='api_change_password'),
    
    # Dashboard & Stats
    path('dashboard/', DashboardAPIView.as_view(), name='api_dashboard'),
    path('statistics/', public_statistics, name='api_statistics'),
    
    # AI endpoints
    path('ai/skill-match/', AISkillMatchView.as_view(), name='api_skill_match'),
    path('ai/learning-path/', AILearningPathView.as_view(), name='api_learning_path'),
    path('ai/moderate-review/', AIReviewModerationView.as_view(), name='api_moderate_review'),
]