"""
Management command to setup initial data for SmartHire
Run: python manage.py setup_initial_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from interviews.models import InterviewQuestion, JobPosition

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial data for SmartHire (interview questions, job positions, HR user)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-hr',
            action='store_true',
            help='Create a default HR user',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting up SmartHire initial data...'))
        
        # Create Interview Questions
        questions = [
            (1, "Tell me about yourself and your background."),
            (2, "Why should we hire you for this position?"),
            (3, "Where do you see yourself five years from now?"),
        ]
        
        questions_created = 0
        for order, text in questions:
            obj, created = InterviewQuestion.objects.get_or_create(
                order=order,
                defaults={'text': text, 'is_active': True}
            )
            if created:
                questions_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'[OK] Interview Questions: {questions_created} created, {len(questions) - questions_created} already exist'
        ))
        
        # Create Job Positions
        positions = [
            ("Software Development Engineer", "Engineering", "Full-stack development role with focus on web technologies."),
            ("Data Scientist", "Analytics", "ML and data analysis role with Python expertise."),
            ("Product Manager", "Product", "Lead product development and strategy."),
            ("DevOps Engineer", "Operations", "Infrastructure and CI/CD pipeline management."),
        ]
        
        positions_created = 0
        for title, department, description in positions:
            obj, created = JobPosition.objects.get_or_create(
                title=title,
                defaults={
                    'department': department,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                positions_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'[OK] Job Positions: {positions_created} created, {len(positions) - positions_created} already exist'
        ))
        
        # Create HR user if requested
        if options['with_hr']:
            hr_user, created = User.objects.get_or_create(
                username='hr_admin',
                defaults={
                    'email': 'hr@smarthire.com',
                    'first_name': 'HR',
                    'last_name': 'Admin',
                    'role': 'hr',
                    'is_staff': True,
                }
            )
            if created:
                hr_user.set_password('hrpassword123')
                hr_user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] HR User created: username=hr_admin, password=hrpassword123'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'! HR User already exists: hr_admin'
                ))
        
        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Initial data setup complete!'))
        self.stdout.write(self.style.NOTICE('\nNext steps:'))
        self.stdout.write('  1. Run: python manage.py runserver')
        self.stdout.write('  2. Visit: http://127.0.0.1:8000')
        self.stdout.write('  3. Register as a candidate or login as HR')

