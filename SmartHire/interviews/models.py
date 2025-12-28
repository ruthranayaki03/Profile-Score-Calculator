"""
Database Models for SmartHire Interview Platform
Properly designed schema with relationships and security
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
import uuid
import os


def resume_upload_path(instance, filename):
    """Generate unique path for resume uploads"""
    ext = filename.split('.')[-1]
    filename = f"{instance.user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('resumes', filename)


def video_upload_path(instance, filename):
    """Generate unique path for video uploads"""
    ext = filename.split('.')[-1]
    filename = f"{instance.interview.id}_q{instance.question_number}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('videos', filename)


class User(AbstractUser):
    """Custom User model with role-based access"""
    
    class Role(models.TextChoices):
        CANDIDATE = 'candidate', 'Candidate'
        HR = 'hr', 'HR/Interviewer'
        ADMIN = 'admin', 'Administrator'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CANDIDATE
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_candidate(self):
        return self.role == self.Role.CANDIDATE

    @property
    def is_hr(self):
        return self.role == self.Role.HR

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class CandidateProfile(models.Model):
    """Extended profile for candidates"""
    
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(65)],
        null=True, blank=True
    )
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    resume = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        null=True, blank=True
    )
    
    # Resume parsed data
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    degree = models.CharField(max_length=200, blank=True)
    designation = models.CharField(max_length=200, blank=True)
    total_experience = models.FloatField(null=True, blank=True)
    
    # Personality Assessment (OCEAN model - 1-10 scale)
    openness = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    conscientiousness = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    extraversion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    agreeableness = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    neuroticism = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    
    # ML Predicted Personality
    predicted_personality = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Candidate Profile'
        verbose_name_plural = 'Candidate Profiles'

    def __str__(self):
        return f"Profile: {self.user.get_full_name() or self.user.username}"


class JobPosition(models.Model):
    """Job positions available for interviews"""
    
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Job Position'
        verbose_name_plural = 'Job Positions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.department}"


class Interview(models.Model):
    """Interview session for a candidate"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        EVALUATED = 'evaluated', 'Evaluated'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
    
    candidate = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='interviews',
        limit_choices_to={'role': 'candidate'}
    )
    position = models.ForeignKey(
        JobPosition, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='interviews'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Analysis Results
    tone_analysis_image = models.ImageField(
        upload_to='analysis/', 
        null=True, 
        blank=True
    )
    emotion_analysis_image = models.ImageField(
        upload_to='analysis/', 
        null=True, 
        blank=True
    )
    
    # Overall Scores (0-100)
    confidence_score = models.FloatField(null=True, blank=True)
    analytical_score = models.FloatField(null=True, blank=True)
    joy_score = models.FloatField(null=True, blank=True)
    fear_score = models.FloatField(null=True, blank=True)
    
    # HR Notes
    hr_notes = models.TextField(blank=True)
    evaluated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluated_interviews',
        limit_choices_to={'role__in': ['hr', 'admin']}
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    
    # Email tracking
    decision_email_sent = models.BooleanField(default=False)
    decision_email_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Interview: {self.candidate.get_full_name()} - {self.position.title if self.position else 'N/A'}"

    def mark_accepted(self, hr_user):
        """Mark interview as accepted"""
        self.status = self.Status.ACCEPTED
        self.evaluated_by = hr_user
        self.evaluated_at = timezone.now()
        self.save()

    def mark_rejected(self, hr_user):
        """Mark interview as rejected"""
        self.status = self.Status.REJECTED
        self.evaluated_by = hr_user
        self.evaluated_at = timezone.now()
        self.save()


class InterviewQuestion(models.Model):
    """Predefined interview questions"""
    
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Interview Question'
        verbose_name_plural = 'Interview Questions'
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}..."


class VideoResponse(models.Model):
    """Video response for each interview question"""
    
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='video_responses'
    )
    question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.SET_NULL,
        null=True
    )
    question_number = models.PositiveIntegerField()
    video_file = models.FileField(
        upload_to=video_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4', 'avi'])]
    )
    
    # Transcribed text from speech
    transcribed_text = models.TextField(blank=True)
    
    # Tone analysis for this response
    analytical_tone = models.FloatField(null=True, blank=True)
    confident_tone = models.FloatField(null=True, blank=True)
    tentative_tone = models.FloatField(null=True, blank=True)
    joy_tone = models.FloatField(null=True, blank=True)
    fear_tone = models.FloatField(null=True, blank=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Video Response'
        verbose_name_plural = 'Video Responses'
        ordering = ['question_number']
        unique_together = ['interview', 'question_number']

    def __str__(self):
        return f"Response Q{self.question_number} - Interview {self.interview.id}"


