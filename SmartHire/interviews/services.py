"""
Business Logic Services for SmartHire
Includes ML prediction, resume parsing, video analysis
"""

import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


class PersonalityPredictor:
    """ML-based personality prediction using Big Five (OCEAN) model"""
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self._train_model()
    
    def _train_model(self):
        """Train the Logistic Regression model"""
        try:
            # Load training dataset
            dataset_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'trainDataset.csv')
            
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                df['Gender'] = self.label_encoder.fit_transform(df['Gender'])
                
                X_train = df.iloc[:, :-1].to_numpy()
                y_train = df.iloc[:, -1].to_numpy(dtype=str)
                
                self.model = LogisticRegression(
                    solver='lbfgs',
                    max_iter=1000
                )
                self.model.fit(X_train, y_train)
                logger.info("Personality prediction model trained successfully")
            else:
                logger.warning(f"Training dataset not found at {dataset_path}")
                self.model = None
        except Exception as e:
            logger.error(f"Error training model: {e}")
            self.model = None
    
    def predict(self, gender: str, age: int, openness: int, neuroticism: int,
                conscientiousness: int, agreeableness: int, extraversion: int) -> str:
        """Predict personality type based on OCEAN scores"""
        if self.model is None:
            return "Unable to predict"
        
        try:
            # Encode gender (1 = male, 0 = female)
            gender_encoded = 1 if gender.lower() == 'male' else 0
            
            input_features = [
                gender_encoded, age, openness, neuroticism,
                conscientiousness, agreeableness, extraversion
            ]
            
            prediction = self.model.predict([input_features])[0]
            return str(prediction).capitalize()
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "Unable to predict"


class ResumeParser:
    """Parse resume and extract relevant information"""
    
    @staticmethod
    def parse(file_path: str) -> dict:
        """Extract data from resume file"""
        try:
            from pyresparser import ResumeParser as PyResParser
            
            data = PyResParser(file_path).get_extracted_data()
            
            # Safely extract data with defaults
            skills = data.get('skills', [])
            skills_str = ', '.join(skills) if skills else ''
            
            degree_list = data.get('degree', [])
            degree = degree_list[0] if degree_list else ''
            
            designation_list = data.get('designation', [])
            designation = designation_list[0] if designation_list else ''
            
            return {
                'mobile_number': data.get('mobile_number', ''),
                'skills': skills_str,
                'degree': degree,
                'designation': designation,
                'total_experience': data.get('total_experience', 0),
                'name': data.get('name', ''),
            }
        except Exception as e:
            logger.error(f"Resume parsing error: {e}")
            return {
                'mobile_number': '',
                'skills': '',
                'degree': '',
                'designation': '',
                'total_experience': 0,
                'name': '',
            }


class EmailService:
    """Handle sending emails to candidates"""
    
    @staticmethod
    def send_acceptance_email(candidate, position_title: str, hr_name: str = "HR Team"):
        """Send job acceptance email"""
        try:
            subject = f"Congratulations! Job Offer - {position_title}"
            
            message = f"""
Dear {candidate.get_full_name()},

Thank you for taking the time to interview for the {position_title} position. We enjoyed getting to know you and were impressed by your skills and experience.

We are pleased to inform you that we would like to offer you the {position_title} position at our company!

We believe your past experience and strong technical skills will be an asset to our organization.

Next Steps:
- Please respond to this email within 7 days to confirm your acceptance
- Our HR team will reach out with more details about the onboarding process

If you have any questions, please don't hesitate to reach out.

We look forward to welcoming you to our team!

Best regards,
{hr_name}
Human Resources Team
SmartHire
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate.email],
                fail_silently=False,
            )
            logger.info(f"Acceptance email sent to {candidate.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send acceptance email: {e}")
            return False
    
    @staticmethod
    def send_rejection_email(candidate, position_title: str, hr_name: str = "HR Team"):
        """Send polite rejection email"""
        try:
            subject = f"Your Application to SmartHire - {position_title}"
            
            message = f"""
Dear {candidate.get_full_name()},

Thank you for taking the time to interview for the {position_title} position at SmartHire. We appreciate your interest in joining our team.

After careful consideration, we have decided to move forward with another candidate whose experience more closely aligns with our current needs.

This was a difficult decision as we were impressed by your qualifications. We encourage you to apply for future openings that match your skills and experience.

We will keep your resume on file and may reach out if a suitable position becomes available.

We wish you all the best in your job search and future career endeavors.

Warm regards,
{hr_name}
Human Resources Team
SmartHire
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate.email],
                fail_silently=False,
            )
            logger.info(f"Rejection email sent to {candidate.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send rejection email: {e}")
            return False


# Singleton instance for personality predictor
_personality_predictor = None

def get_personality_predictor():
    """Get or create personality predictor instance"""
    global _personality_predictor
    if _personality_predictor is None:
        _personality_predictor = PersonalityPredictor()
    return _personality_predictor


