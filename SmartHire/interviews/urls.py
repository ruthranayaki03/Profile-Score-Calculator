"""
URL patterns for SmartHire Interview Platform
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.CandidateRegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Candidate URLs
    path('candidate/', views.CandidateDashboardView.as_view(), name='candidate_dashboard'),
    path('candidate/profile/', views.CandidateProfileView.as_view(), name='candidate_profile'),
    path('candidate/interview/start/', views.StartInterviewView.as_view(), name='candidate_start_interview'),
    path('candidate/interview/<int:interview_id>/questions/', 
         views.InterviewQuestionsView.as_view(), name='interview_questions'),
    path('candidate/interview/<int:interview_id>/submit/', 
         views.SubmitVideoResponseView.as_view(), name='submit_video'),
    path('candidate/interview/complete/', 
         views.InterviewCompleteView.as_view(), name='interview_complete'),
    path('candidate/interview/<int:interview_id>/status/', 
         views.CandidateInterviewStatusView.as_view(), name='candidate_interview_status'),
    
    # HR URLs
    path('hr/', views.HRDashboardView.as_view(), name='hr_dashboard'),
    path('hr/candidates/', views.CandidateListView.as_view(), name='candidate_list'),
    path('hr/candidates/<int:interview_id>/', 
         views.CandidateDetailView.as_view(), name='candidate_detail'),
    path('hr/candidates/<int:interview_id>/evaluate/', 
         views.EvaluateInterviewView.as_view(), name='evaluate_interview'),
    path('hr/candidates/<int:interview_id>/accept/', 
         views.SendAcceptanceEmailView.as_view(), name='send_acceptance'),
    path('hr/candidates/<int:interview_id>/reject/', 
         views.SendRejectionEmailView.as_view(), name='send_rejection'),
    
    # Job Position Management
    path('hr/positions/', views.JobPositionListView.as_view(), name='position_list'),
    path('hr/positions/create/', views.JobPositionCreateView.as_view(), name='position_create'),
    path('hr/positions/<int:pk>/edit/', views.JobPositionUpdateView.as_view(), name='position_update'),
    
    # Interview Questions Management
    path('hr/questions/', views.InterviewQuestionListView.as_view(), name='question_list'),
]


