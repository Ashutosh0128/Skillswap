from django.contrib import admin
from .models import SkillCategory, Skill, SkillOffer, Session, Review


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty', 'created_at']
    list_filter = ['category', 'difficulty']
    search_fields = ['name', 'description']


@admin.register(SkillOffer)
class SkillOfferAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'hourly_rate', 'is_active', 'created_at']
    list_filter = ['is_active', 'skill__category']
    search_fields = ['teacher__user__username', 'skill__name']
    list_editable = ['is_active']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status', 'scheduled_date', 'scheduled_time', 'duration']
    list_filter = ['status', 'skill__category']
    search_fields = ['teacher__user__username', 'learner__user__username', 'skill__name']
    readonly_fields = ['ai_summary', 'created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'rating', 'ai_flagged', 'created_at']
    list_filter = ['rating', 'ai_flagged']
    search_fields = ['reviewer__user__username', 'reviewee__user__username']
    readonly_fields = ['created_at']