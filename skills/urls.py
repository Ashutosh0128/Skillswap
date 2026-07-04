from django.urls import path
from . import views

app_name = 'skills'

urlpatterns = [
    # Categories
    path('categories/', views.SkillCategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.SkillCategoryDetailView.as_view(), name='category_detail'),

    # Skills
    path('', views.SkillListView.as_view(), name='skill_list'),
    path('create/', views.SkillCreateView.as_view(), name='skill_create'),
    path('<int:pk>/', views.SkillDetailView.as_view(), name='skill_detail'),
    path('<int:pk>/update/', views.SkillUpdateView.as_view(), name='skill_update'),
    path('<int:pk>/delete/', views.SkillDeleteView.as_view(), name='skill_delete'),

    # Offers
    path('offers/', views.SkillOfferListView.as_view(), name='offer_list'),
    path('offers/create/', views.SkillOfferCreateView.as_view(), name='offer_create'),
    path('offers/<int:pk>/', views.SkillOfferDetailView.as_view(), name='offer_detail'),
    path('offers/<int:pk>/update/', views.SkillOfferUpdateView.as_view(), name='offer_update'),
    path('offers/<int:pk>/delete/', views.SkillOfferDeleteView.as_view(), name='offer_delete'),
    path('offers/<int:offer_id>/book/', views.SessionBookingView.as_view(), name='session_book'),

    # Sessions
    path('sessions/', views.MySessionsView.as_view(), name='my_sessions'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/update/', views.SessionUpdateView.as_view(), name='session_update'),

    # Reviews
    path('sessions/<int:session_id>/review/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/update/', views.ReviewUpdateView.as_view(), name='review_update'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),
]