from celery import Task
from backend.celery_app import celery_app
from backend.services.gpt_service import gpt_service
from typing import List, Dict, Any
import tempfile
import os
import asyncio
from datetime import datetime
import base64

# Import text extraction functions
# These will be imported from main module at runtime
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return ""

def extract_email_from_text(text: str) -> str:
    """Extract email address from text"""
    import re
    email_pattern = r'\b[A-Za-z0-9]([A-Za-z0-9._%-]*[A-Za-z0-9])?@[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        return emails[0] if isinstance(emails[0], str) else emails[0][0]
    return ""

def extract_name_from_text(text: str) -> str:
    """Extract name from resume text"""
    lines = text.split('\n')
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        if not line:
            continue
        skip_words = ['resume', 'cv', 'curriculum', 'vitae', 'contact', 'personal', 'information', 'profile', 'objective']
        if any(word in line.lower() for word in skip_words):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(word[0].isupper() and word.isalpha() for word in words):
                if not any(word.lower() in ['phone', 'email', 'address', 'linkedin', 'github', 'portfolio'] for word in words):
                    return ' '.join(words)
    return "Unknown"

def extract_phone_from_text(text: str) -> str:
    """Extract phone number from text"""
    import re
    phone_patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        r'\+?[0-9]{1,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            clean_phone = re.sub(r'[^\d+]', '', phones[0])
            if 7 <= len(clean_phone.replace('+', '')) <= 15:
                return phones[0]
    return ""

def validate_extracted_data(name: str, email: str, phone: str) -> dict:
    """Validate and clean extracted data"""
    import re
    validated = {'name': name, 'email': email, 'phone': phone}
    
    if name and name != "Unknown":
        if re.match(r'^[a-zA-Z\s]+$', name):
            validated['name'] = name.strip().title()
        else:
            validated['name'] = "Unknown"
    
    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            validated['email'] = email.strip().lower()
        else:
            validated['email'] = ""
    
    if phone:
        clean_phone = re.sub(r'[^\d+]', '', phone)
        if 7 <= len(clean_phone.replace('+', '')) <= 15:
            validated['phone'] = clean_phone
        else:
            validated['phone'] = ""
    
    return validated

def categorize_resume(score: float) -> str:
    """Categorize resume based on score"""
    if score >= 7.0:
        return "selected"
    elif score >= 4.0:
        return "considered"
    else:
        return "rejected"

# Import services
try:
    from firebase_service import firebase_service
    FIREBASE_AVAILABLE = True
except:
    FIREBASE_AVAILABLE = False

try:
    from s3_service import s3_service
    S3_AVAILABLE = True
except:
    S3_AVAILABLE = False

class ProcessResumeTask(Task):
    """Custom task class with progress tracking"""
    def on_success(self, retval, task_id, args, kwargs):
        print(f"Task {task_id} succeeded: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed: {exc}")

@celery_app.task(
    bind=True,
    base=ProcessResumeTask,
    name='backend.tasks.resume_tasks.process_resume_batch'
)
def process_resume_batch(
    self,
    resume_files_data: List[Dict[str, Any]],
    job_description: str,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Process a batch of resumes in the background
    
    Args:
        resume_files_data: List of dicts with 'filename', 'content' (base64 encoded), 'file_type'
        job_description: Job description text
        user_id: User ID for storing results
    
    Returns:
        Dict with processed results
    """
    results = {
        "selected": [],
        "rejected": [],
        "considered": []
    }
    
    total = len(resume_files_data)
    processed = 0
    
    # Process resumes in parallel batches
    batch_size = 5  # Process 5 resumes at a time
    
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = resume_files_data[batch_start:batch_end]
        
        # Process batch in parallel
        batch_results = []
        for resume_data in batch:
            try:
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': processed,
                        'total': total,
                        'status': f'Processing {resume_data["filename"]}'
                    }
                )
                
                # Decode base64 content
                content = base64.b64decode(resume_data['content'])
                file_type = resume_data['file_type']
                filename = resume_data['filename']
                
                # Save temporarily for text extraction
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    # Extract text based on file type
                    if file_type == 'pdf':
                        text = extract_text_from_pdf(temp_file_path)
                    elif file_type in ['doc', 'docx']:
                        text = extract_text_from_docx(temp_file_path)
                    else:
                        text = content.decode('utf-8', errors='ignore')
                    
                    # Extract basic information
                    email = extract_email_from_text(text)
                    name = extract_name_from_text(text)
                    phone = extract_phone_from_text(text)
                    
                    # Validate data
                    validated_data = validate_extracted_data(name, email, phone)
                    
                    # Upload to S3
                    s3_url = None
                    if S3_AVAILABLE and user_id:
                        try:
                            s3_url = s3_service.upload_resume_from_bytes(
                                content,
                                user_id,
                                filename
                            )
                        except Exception as e:
                            print(f"S3 upload failed: {e}")
                    
                    # Analyze with GPT (async)
                    analysis = asyncio.run(
                        gpt_service.analyze_resume_async(text, job_description)
                    )
                    
                    score = analysis["score"]
                    category = categorize_resume(score)
                    
                    # Create resume data
                    resume_result = {
                        "id": f"resume_{processed}",
                        "name": validated_data['name'],
                        "email": validated_data['email'],
                        "phone": validated_data['phone'],
                        "s3_url": s3_url,
                        "fileName": filename,
                        "score": score,
                        "category": category,
                        "content": text,
                        "explanation": analysis.get("explanation", ""),
                        "strengths": analysis.get("strengths", []),
                        "weaknesses": analysis.get("weaknesses", [])
                    }
                    
                    batch_results.append((category, resume_result))
                    
                    # Store in Firebase if user_id provided
                    if FIREBASE_AVAILABLE and user_id:
                        try:
                            firebase_service.store_resume_data(user_id, {
                                "candidateName": validated_data['name'],
                                "candidateEmail": validated_data['email'],
                                "candidatePhone": validated_data['phone'],
                                "s3Url": s3_url,
                                "fileName": filename,
                                "category": category,
                                "score": score,
                                "content": text,
                                "explanation": analysis.get("explanation", ""),
                                "strengths": analysis.get("strengths", []),
                                "weaknesses": analysis.get("weaknesses", []),
                                "uploadedAt": datetime.now()
                            })
                            
                            # Store uploaded file info
                            file_data = {
                                "fileName": filename,
                                "fileSize": len(content),
                                "fileType": file_type,
                                "s3Url": s3_url,
                                "status": "processed"
                            }
                            firebase_service.store_uploaded_file(user_id, file_data)
                        except Exception as e:
                            print(f"Firebase storage failed: {e}")
                    
                    processed += 1
                    
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
                        
            except Exception as e:
                print(f"Error processing resume: {e}")
                import traceback
                traceback.print_exc()
                # Add fallback entry
                batch_results.append(("rejected", {
                    "id": f"resume_{processed}",
                    "name": "Unknown",
                    "email": "",
                    "phone": "",
                    "s3_url": None,
                    "fileName": resume_data.get("filename", "unknown"),
                    "score": 0.0,
                    "category": "rejected",
                    "explanation": f"Error processing resume: {str(e)}",
                    "strengths": [],
                    "weaknesses": []
                }))
                processed += 1
        
        # Add batch results to main results
        for category, resume_result in batch_results:
            results[category].append(resume_result)
    
    return {
        "data": results,
        "metadata": {
            "total_processed": processed,
            "processed_at": datetime.now().isoformat(),
            "user_id": user_id
        }
    }

