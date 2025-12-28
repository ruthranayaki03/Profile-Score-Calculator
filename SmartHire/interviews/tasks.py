"""
Celery Tasks for SmartHire
Async video processing and analysis
"""

import os
import time
import random
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_random_job_name(length=10):
    """Generate random job name for AWS Transcribe"""
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(length))


@shared_task(bind=True, max_retries=3)
def process_video_response(self, video_response_id):
    """
    Async task to process a single video response:
    1. Upload to AWS S3
    2. Transcribe using AWS Transcribe
    3. Analyze tone using IBM Watson
    """
    from .models import VideoResponse
    
    try:
        video_response = VideoResponse.objects.get(id=video_response_id)
        video_path = video_response.video_file.path
        
        # Step 1: Extract text using AWS Transcribe
        transcribed_text = transcribe_video(video_path)
        video_response.transcribed_text = transcribed_text
        
        # Step 2: Analyze tone using IBM Watson
        if transcribed_text:
            tones = analyze_tone(transcribed_text)
            video_response.analytical_tone = tones.get('Analytical', 0)
            video_response.confident_tone = tones.get('Confident', 0)
            video_response.tentative_tone = tones.get('Tentative', 0)
            video_response.joy_tone = tones.get('Joy', 0)
            video_response.fear_tone = tones.get('Fear', 0)
        
        video_response.is_processed = True
        video_response.save()
        
        # Check if all responses for this interview are processed
        interview = video_response.interview
        all_processed = not interview.video_responses.filter(is_processed=False).exists()
        
        if all_processed:
            # Generate analysis charts
            generate_analysis_charts.delay(interview.id)
        
        logger.info(f"Video response {video_response_id} processed successfully")
        return True
        
    except VideoResponse.DoesNotExist:
        logger.error(f"VideoResponse {video_response_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error processing video {video_response_id}: {e}")
        video_response.processing_error = str(e)
        video_response.save()
        raise self.retry(exc=e, countdown=60)


def transcribe_video(video_path: str) -> str:
    """Transcribe video using AWS Transcribe"""
    try:
        import boto3
        
        if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.AWS_S3_BUCKET]):
            logger.warning("AWS credentials not configured, using mock transcription")
            return "Mock transcription - AWS not configured"
        
        # Create S3 client
        s3 = boto3.resource(
            service_name="s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Upload to S3
        filename = os.path.basename(video_path)
        s3.Bucket(settings.AWS_S3_BUCKET).upload_file(Filename=video_path, Key=filename)
        
        # Create Transcribe client
        transcribe = boto3.Session(
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        ).client("transcribe")
        
        # Start transcription job
        job_name = f"smarthire_{generate_random_job_name()}"
        job_uri = f"s3://{settings.AWS_S3_BUCKET}/{filename}"
        
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='webm',
            LanguageCode=settings.AWS_LANG_CODE
        )
        
        # Wait for completion (with timeout)
        max_wait = 300  # 5 minutes
        waited = 0
        while waited < max_wait:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            
            if job_status == 'COMPLETED':
                data = pd.read_json(status['TranscriptionJob']['Transcript']['TranscriptFileUri'])
                text = data['results'][1][0]['transcript']
                
                # Cleanup S3
                s3.Bucket(settings.AWS_S3_BUCKET).objects.filter(Prefix=filename).delete()
                return text
                
            elif job_status == 'FAILED':
                logger.error(f"Transcription job {job_name} failed")
                return ""
            
            time.sleep(10)
            waited += 10
        
        logger.error(f"Transcription job {job_name} timed out")
        return ""
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""


def analyze_tone(text: str) -> dict:
    """Analyze tone using IBM Watson"""
    try:
        from ibm_watson import ToneAnalyzerV3
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        
        if not all([settings.IBM_API_KEY, settings.IBM_URL]):
            logger.warning("IBM Watson credentials not configured, using mock analysis")
            return {
                'Analytical': random.uniform(20, 80),
                'Confident': random.uniform(20, 80),
                'Tentative': random.uniform(10, 40),
                'Joy': random.uniform(20, 60),
                'Fear': random.uniform(5, 30),
            }
        
        authenticator = IAMAuthenticator(settings.IBM_API_KEY)
        tone_analyzer = ToneAnalyzerV3(version='2017-09-21', authenticator=authenticator)
        tone_analyzer.set_service_url(settings.IBM_URL)
        
        result = tone_analyzer.tone(text).get_result()
        
        tones = {}
        for tone in result.get('document_tone', {}).get('tones', []):
            tones[tone['tone_name']] = round(tone['score'] * 100, 2)
        
        # Ensure all expected tones have a value
        for tone_name in ['Analytical', 'Confident', 'Tentative', 'Joy', 'Fear']:
            if tone_name not in tones:
                tones[tone_name] = 0.0
        
        return tones
        
    except Exception as e:
        logger.error(f"Tone analysis error: {e}")
        return {'Analytical': 0, 'Confident': 0, 'Tentative': 0, 'Joy': 0, 'Fear': 0}


@shared_task(bind=True)
def generate_analysis_charts(self, interview_id):
    """Generate tone and emotion analysis charts for interview"""
    from .models import Interview
    
    try:
        interview = Interview.objects.get(id=interview_id)
        responses = interview.video_responses.order_by('question_number')
        
        if not responses.exists():
            logger.warning(f"No video responses for interview {interview_id}")
            return False
        
        # Prepare data for tone analysis chart
        questions = []
        analytical = []
        confident = []
        fear = []
        joy = []
        tentative = []
        
        for i, response in enumerate(responses, 1):
            questions.append(f'Q{i}')
            analytical.append(response.analytical_tone or 0)
            confident.append(response.confident_tone or 0)
            fear.append(response.fear_tone or 0)
            joy.append(response.joy_tone or 0)
            tentative.append(response.tentative_tone or 0)
        
        # Create tone analysis chart
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(questions))
        width = 0.15
        
        ax.bar(x - 2*width, analytical, width, label='Analytical', color='#3498db')
        ax.bar(x - width, confident, width, label='Confident', color='#2ecc71')
        ax.bar(x, fear, width, label='Fear', color='#e74c3c')
        ax.bar(x + width, joy, width, label='Joy', color='#f39c12')
        ax.bar(x + 2*width, tentative, width, label='Tentative', color='#9b59b6')
        
        ax.set_xlabel('Questions', fontsize=12)
        ax.set_ylabel('Score (%)', fontsize=12)
        ax.set_title('Tone Analysis by Question', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(questions)
        ax.legend(loc='upper right')
        ax.set_ylim(0, 100)
        
        sns.set_style("whitegrid")
        
        # Save tone analysis chart
        tone_chart_path = os.path.join(settings.MEDIA_ROOT, 'analysis', f'tone_{interview_id}.png')
        os.makedirs(os.path.dirname(tone_chart_path), exist_ok=True)
        plt.savefig(tone_chart_path, bbox_inches='tight', dpi=150)
        plt.close()
        
        # Update interview with chart path
        interview.tone_analysis_image = f'analysis/tone_{interview_id}.png'
        
        # Calculate overall scores
        interview.analytical_score = np.mean(analytical)
        interview.confidence_score = np.mean(confident)
        interview.fear_score = np.mean(fear)
        interview.joy_score = np.mean(joy)
        
        interview.status = 'completed'
        interview.save()
        
        logger.info(f"Analysis charts generated for interview {interview_id}")
        return True
        
    except Interview.DoesNotExist:
        logger.error(f"Interview {interview_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error generating charts: {e}")
        raise


@shared_task
def process_face_emotions(interview_id):
    """Process face emotions from combined video"""
    from .models import Interview
    
    try:
        interview = Interview.objects.get(id=interview_id)
        responses = interview.video_responses.order_by('question_number')
        
        if not responses.exists():
            return False
        
        # Combine videos
        video_paths = [r.video_file.path for r in responses if r.video_file]
        
        if not video_paths:
            return False
        
        # Use FER for emotion detection
        try:
            from fer import Video, FER
            
            # Create combined video
            combined_path = os.path.join(settings.MEDIA_ROOT, 'videos', f'combined_{interview_id}.webm')
            
            frame_per_sec = 30
            size = (1280, 720)
            
            video_writer = cv2.VideoWriter(
                combined_path,
                cv2.VideoWriter_fourcc(*"VP90"),
                frame_per_sec,
                size
            )
            
            for vpath in video_paths:
                cap = cv2.VideoCapture(vpath)
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame = cv2.resize(frame, size)
                    video_writer.write(frame)
                cap.release()
            
            video_writer.release()
            
            # Analyze emotions
            face_detector = FER(mtcnn=True)
            input_video = Video(combined_path)
            processing_data = input_video.analyze(
                face_detector,
                display=False,
                save_frames=False,
                save_video=False,
                annotate_frames=False,
                zip_images=False
            )
            
            vid_df = input_video.to_pandas(processing_data)
            vid_df = input_video.get_first_face(vid_df)
            vid_df = input_video.get_emotions(vid_df)
            
            # Save emotion chart
            fig = vid_df.plot(figsize=(12, 6), fontsize=12).get_figure()
            plt.legend(fontsize='large', loc=1)
            
            emotion_chart_path = os.path.join(settings.MEDIA_ROOT, 'analysis', f'emotion_{interview_id}.png')
            fig.savefig(emotion_chart_path, bbox_inches='tight', dpi=150)
            plt.close()
            
            interview.emotion_analysis_image = f'analysis/emotion_{interview_id}.png'
            interview.save()
            
            # Cleanup combined video
            if os.path.exists(combined_path):
                os.remove(combined_path)
            
            return True
            
        except ImportError:
            logger.warning("FER library not available")
            return False
            
    except Exception as e:
        logger.error(f"Face emotion processing error: {e}")
        return False


