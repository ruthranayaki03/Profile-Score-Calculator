"""
Django Admin configuration for SmartHire
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, CandidateProfile, JobPosition, 
    Interview, InterviewQuestion, VideoResponse
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'gender', 'predicted_personality', 'created_at']
    list_filter = ['gender', 'predicted_personality']
    search_fields = ['user__username', 'user__email', 'skills']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'is_active', 'created_at']
    list_filter = ['department', 'is_active']
    search_fields = ['title', 'department']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'position', 'status', 'evaluated_by', 'created_at']
    list_filter = ['status', 'position', 'created_at']
    search_fields = ['candidate__username', 'candidate__email']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['candidate', 'evaluated_by']


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ['order', 'text', 'is_active']
    list_filter = ['is_active']
    ordering = ['order']


@admin.register(VideoResponse)
class VideoResponseAdmin(admin.ModelAdmin):
    list_display = ['interview', 'question_number', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'created_at']
    readonly_fields = ['created_at']


