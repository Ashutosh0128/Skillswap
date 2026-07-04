from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'is_verified', 'get_average_rating', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'location', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_verified']