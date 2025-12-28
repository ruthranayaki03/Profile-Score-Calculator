"""
Django Forms for SmartHire Interview Platform
With proper validation and security
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import FileExtensionValidator
from .models import User, CandidateProfile, Interview, JobPosition


class CandidateRegistrationForm(UserCreationForm):
    """Registration form for candidates"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = User.Role.CANDIDATE
        if commit:
            user.save()
            # Create empty profile (use get_or_create to avoid duplicates)
            CandidateProfile.objects.get_or_create(user=user)
        return user


class HRLoginForm(AuthenticationForm):
    """Login form for HR/Admin users"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email or Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class CandidateProfileForm(forms.ModelForm):
    """Form for candidate to fill their profile and personality assessment"""
    
    class Meta:
        model = CandidateProfile
        fields = [
            'age', 'gender', 'resume',
            'openness', 'conscientiousness', 'extraversion',
            'agreeableness', 'neuroticism'
        ]
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 18,
                'max': 65,
                'placeholder': 'Age'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'openness': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
            'conscientiousness': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
            'extraversion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
            'agreeableness': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
            'neuroticism': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
        }
        labels = {
            'openness': 'How much do you enjoy new experiences? (Openness)',
            'conscientiousness': 'How thorough are you in your work? (Conscientiousness)',
            'extraversion': 'How outgoing and social are you? (Extraversion)',
            'agreeableness': 'How much do you enjoy working with peers? (Agreeableness)',
            'neuroticism': 'How often do you feel negativity? (Neuroticism)',
        }


class UserProfileUpdateForm(forms.ModelForm):
    """Form to update user's basic info"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class InterviewEvaluationForm(forms.ModelForm):
    """Form for HR to evaluate interview"""
    
    class Meta:
        model = Interview
        fields = ['hr_notes', 'status']
        widgets = {
            'hr_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add notes about this candidate...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class JobPositionForm(forms.ModelForm):
    """Form to create/edit job positions"""
    
    class Meta:
        model = JobPosition
        fields = ['title', 'department', 'description', 'requirements', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


