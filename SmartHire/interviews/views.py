"""
Django Views for SmartHire Interview Platform
With proper authentication and security
"""

import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    View, TemplateView, ListView, DetailView, 
    CreateView, UpdateView
)
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.core.files.storage import default_storage

from .models import (
    User, CandidateProfile, JobPosition, 
    Interview, InterviewQuestion, VideoResponse
)
from .forms import (
    CandidateRegistrationForm, HRLoginForm, 
    CandidateProfileForm, UserProfileUpdateForm,
    InterviewEvaluationForm, JobPositionForm
)
from .services import (
    get_personality_predictor, ResumeParser, EmailService
)


# =============================================================================
# MIXINS
# =============================================================================

class CandidateMixin(UserPassesTestMixin):
    """Ensure user is a candidate"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_candidate


class HRMixin(UserPassesTestMixin):
    """Ensure user is HR or Admin"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_hr or self.request.user.is_admin_user or self.request.user.is_superuser
        )


# =============================================================================
# PUBLIC VIEWS
# =============================================================================

class HomeView(TemplateView):
    """Landing page with login/signup"""
    template_name = 'home.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_candidate:
                return redirect('candidate_dashboard')
            else:
                return redirect('hr_dashboard')
        return super().get(request, *args, **kwargs)


class CandidateRegisterView(View):
    """Candidate registration"""
    template_name = 'registration/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('candidate_dashboard')
        form = CandidateRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = CandidateRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Please complete your profile.')
            return redirect('candidate_profile')
        return render(request, self.template_name, {'form': form})


class CustomLoginView(View):
    """Custom login for both candidates and HR"""
    template_name = 'registration/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = HRLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = HRLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            
            # Redirect based on role
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            if user.is_candidate:
                return redirect('candidate_dashboard')
            else:
                return redirect('hr_dashboard')
        
        messages.error(request, 'Invalid credentials. Please try again.')
        return render(request, self.template_name, {'form': form})


class CustomLogoutView(View):
    """Logout view"""
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('home')
    
    def post(self, request):
        return self.get(request)


@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on role"""
    if request.user.is_candidate:
        return redirect('candidate_dashboard')
    else:
        return redirect('hr_dashboard')


# =============================================================================
# CANDIDATE VIEWS
# =============================================================================

class CandidateDashboardView(LoginRequiredMixin, CandidateMixin, TemplateView):
    """Candidate dashboard"""
    template_name = 'candidate/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['interviews'] = self.request.user.interviews.all()[:5]
        context['profile'] = getattr(self.request.user, 'profile', None)
        return context


class CandidateProfileView(LoginRequiredMixin, CandidateMixin, View):
    """Candidate profile and personality assessment"""
    template_name = 'candidate/profile.html'
    
    def get(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        user_form = UserProfileUpdateForm(instance=request.user)
        profile_form = CandidateProfileForm(instance=profile)
        
        # Get available positions
        positions = JobPosition.objects.filter(is_active=True)
        
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
            'positions': positions,
        })
    
    def post(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        user_form = UserProfileUpdateForm(request.POST, instance=request.user)
        profile_form = CandidateProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            
            # Parse resume if uploaded
            if 'resume' in request.FILES:
                resume_path = profile.resume.path
                parsed_data = ResumeParser.parse(resume_path)
                profile.skills = parsed_data.get('skills', '')
                profile.degree = parsed_data.get('degree', '')
                profile.designation = parsed_data.get('designation', '')
                profile.total_experience = parsed_data.get('total_experience', 0)
                
                # Update phone if found
                if parsed_data.get('mobile_number'):
                    request.user.phone = parsed_data['mobile_number']
                    request.user.save()
            
            # Predict personality
            if all([profile.openness, profile.neuroticism, profile.conscientiousness,
                    profile.agreeableness, profile.extraversion, profile.age, profile.gender]):
                predictor = get_personality_predictor()
                profile.predicted_personality = predictor.predict(
                    gender=profile.gender,
                    age=profile.age,
                    openness=profile.openness,
                    neuroticism=profile.neuroticism,
                    conscientiousness=profile.conscientiousness,
                    agreeableness=profile.agreeableness,
                    extraversion=profile.extraversion
                )
            
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('candidate_start_interview')
        
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
        })


class StartInterviewView(LoginRequiredMixin, CandidateMixin, View):
    """Start a new interview session"""
    template_name = 'candidate/start_interview.html'
    
    def get(self, request):
        # Check if profile is complete
        profile = getattr(request.user, 'profile', None)
        if not profile or not profile.resume:
            messages.warning(request, 'Please complete your profile before starting the interview.')
            return redirect('candidate_profile')
        
        positions = JobPosition.objects.filter(is_active=True)
        questions = InterviewQuestion.objects.filter(is_active=True).order_by('order')
        
        return render(request, self.template_name, {
            'positions': positions,
            'questions': list(questions.values('id', 'text', 'order')),
        })
    
    def post(self, request):
        position_id = request.POST.get('position')
        position = get_object_or_404(JobPosition, id=position_id, is_active=True)
        
        # Create interview
        interview = Interview.objects.create(
            candidate=request.user,
            position=position,
            status=Interview.Status.IN_PROGRESS
        )
        
        messages.success(request, f'Interview started for {position.title}')
        return redirect('interview_questions', interview_id=interview.id)


class InterviewQuestionsView(LoginRequiredMixin, CandidateMixin, View):
    """Video recording for interview questions"""
    template_name = 'candidate/interview_questions.html'
    
    def get(self, request, interview_id):
        interview = get_object_or_404(
            Interview, 
            id=interview_id, 
            candidate=request.user,
            status=Interview.Status.IN_PROGRESS
        )
        questions = InterviewQuestion.objects.filter(is_active=True).order_by('order')
        
        return render(request, self.template_name, {
            'interview': interview,
            'questions': questions,
            'questions_json': json.dumps(list(questions.values('id', 'text', 'order'))),
        })


class SubmitVideoResponseView(LoginRequiredMixin, CandidateMixin, View):
    """Submit video responses"""
    
    def post(self, request, interview_id):
        interview = get_object_or_404(
            Interview,
            id=interview_id,
            candidate=request.user,
            status=Interview.Status.IN_PROGRESS
        )
        
        questions = InterviewQuestion.objects.filter(is_active=True).order_by('order')
        
        # Save video files
        for i, question in enumerate(questions, 1):
            video_key = f'question{i}'
            if video_key in request.FILES:
                video_file = request.FILES[video_key]
                
                video_response, created = VideoResponse.objects.update_or_create(
                    interview=interview,
                    question_number=i,
                    defaults={
                        'question': question,
                        'video_file': video_file,
                    }
                )
                
                # Queue async processing
                try:
                    from .tasks import process_video_response
                    process_video_response.delay(video_response.id)
                except Exception as e:
                    # If Celery not available, mark as needing manual processing
                    video_response.processing_error = f"Async processing not available: {e}"
                    video_response.save()
        
        # Update interview status
        interview.status = Interview.Status.COMPLETED
        interview.save()
        
        return JsonResponse({'status': 'success', 'redirect': reverse_lazy('interview_complete')})


class InterviewCompleteView(LoginRequiredMixin, CandidateMixin, TemplateView):
    """Interview completion thank you page"""
    template_name = 'candidate/interview_complete.html'


class CandidateInterviewStatusView(LoginRequiredMixin, CandidateMixin, DetailView):
    """View interview status and results (for candidate)"""
    template_name = 'candidate/interview_status.html'
    context_object_name = 'interview'
    
    def get_object(self):
        return get_object_or_404(
            Interview,
            id=self.kwargs['interview_id'],
            candidate=self.request.user
        )


# =============================================================================
# HR/ADMIN VIEWS
# =============================================================================

class HRDashboardView(LoginRequiredMixin, HRMixin, TemplateView):
    """HR Dashboard with statistics"""
    template_name = 'hr/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        interviews = Interview.objects.all()
        context['total_interviews'] = interviews.count()
        context['pending_interviews'] = interviews.filter(status=Interview.Status.COMPLETED).count()
        context['accepted_count'] = interviews.filter(status=Interview.Status.ACCEPTED).count()
        context['rejected_count'] = interviews.filter(status=Interview.Status.REJECTED).count()
        
        context['recent_interviews'] = interviews.order_by('-created_at')[:10]
        context['positions'] = JobPosition.objects.filter(is_active=True)
        
        return context


class CandidateListView(LoginRequiredMixin, HRMixin, ListView):
    """List all candidates with their interviews"""
    template_name = 'hr/candidate_list.html'
    context_object_name = 'interviews'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Interview.objects.select_related(
            'candidate', 'candidate__profile', 'position'
        ).order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by position
        position_id = self.request.GET.get('position')
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(candidate__first_name__icontains=search) |
                Q(candidate__last_name__icontains=search) |
                Q(candidate__email__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['positions'] = JobPosition.objects.filter(is_active=True)
        context['status_choices'] = Interview.Status.choices
        return context


class CandidateDetailView(LoginRequiredMixin, HRMixin, DetailView):
    """Detailed view of a candidate's interview"""
    template_name = 'hr/candidate_detail.html'
    context_object_name = 'interview'
    
    def get_object(self):
        return get_object_or_404(
            Interview.objects.select_related('candidate', 'candidate__profile', 'position'),
            id=self.kwargs['interview_id']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interview = self.get_object()
        context['video_responses'] = interview.video_responses.order_by('question_number')
        context['evaluation_form'] = InterviewEvaluationForm(instance=interview)
        return context


class EvaluateInterviewView(LoginRequiredMixin, HRMixin, View):
    """Evaluate and update interview status"""
    
    def post(self, request, interview_id):
        interview = get_object_or_404(Interview, id=interview_id)
        form = InterviewEvaluationForm(request.POST, instance=interview)
        
        if form.is_valid():
            interview = form.save(commit=False)
            interview.evaluated_by = request.user
            interview.evaluated_at = timezone.now()
            interview.save()
            
            messages.success(request, 'Interview evaluation saved.')
        else:
            messages.error(request, 'Error saving evaluation.')
        
        return redirect('candidate_detail', interview_id=interview_id)


class SendAcceptanceEmailView(LoginRequiredMixin, HRMixin, View):
    """Send acceptance email to candidate"""
    
    def post(self, request, interview_id):
        interview = get_object_or_404(Interview, id=interview_id)
        
        success = EmailService.send_acceptance_email(
            candidate=interview.candidate,
            position_title=interview.position.title if interview.position else "Position",
            hr_name=request.user.get_full_name() or "HR Team"
        )
        
        if success:
            interview.mark_accepted(request.user)
            interview.decision_email_sent = True
            interview.decision_email_sent_at = timezone.now()
            interview.save()
            return JsonResponse({'status': 'success', 'message': 'Acceptance email sent!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to send email.'}, status=500)


class SendRejectionEmailView(LoginRequiredMixin, HRMixin, View):
    """Send rejection email to candidate"""
    
    def post(self, request, interview_id):
        interview = get_object_or_404(Interview, id=interview_id)
        
        success = EmailService.send_rejection_email(
            candidate=interview.candidate,
            position_title=interview.position.title if interview.position else "Position",
            hr_name=request.user.get_full_name() or "HR Team"
        )
        
        if success:
            interview.mark_rejected(request.user)
            interview.decision_email_sent = True
            interview.decision_email_sent_at = timezone.now()
            interview.save()
            return JsonResponse({'status': 'success', 'message': 'Rejection email sent!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to send email.'}, status=500)


# =============================================================================
# JOB POSITION MANAGEMENT
# =============================================================================

class JobPositionListView(LoginRequiredMixin, HRMixin, ListView):
    """List job positions"""
    template_name = 'hr/position_list.html'
    model = JobPosition
    context_object_name = 'positions'


class JobPositionCreateView(LoginRequiredMixin, HRMixin, CreateView):
    """Create new job position"""
    template_name = 'hr/position_form.html'
    model = JobPosition
    form_class = JobPositionForm
    success_url = reverse_lazy('position_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Job position created successfully!')
        return super().form_valid(form)


class JobPositionUpdateView(LoginRequiredMixin, HRMixin, UpdateView):
    """Update job position"""
    template_name = 'hr/position_form.html'
    model = JobPosition
    form_class = JobPositionForm
    success_url = reverse_lazy('position_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Job position updated successfully!')
        return super().form_valid(form)


# =============================================================================
# INTERVIEW QUESTION MANAGEMENT
# =============================================================================

class InterviewQuestionListView(LoginRequiredMixin, HRMixin, ListView):
    """List interview questions"""
    template_name = 'hr/question_list.html'
    model = InterviewQuestion
    context_object_name = 'questions'
    ordering = ['order']


