# Phase 1 Implementation Guide - Foundation

This guide provides step-by-step instructions for implementing Phase 1 of the scalability plan.

## Prerequisites

- Python 3.9+
- Redis server (local or cloud)
- Understanding of async/await in Python
- Basic knowledge of Celery

---

## Step 1: Set Up Redis

### Option A: Local Redis (Development)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using Homebrew (macOS)
brew install redis
brew services start redis
```

### Option B: Cloud Redis (Production)

- **AWS ElastiCache**: Managed Redis service
- **Redis Cloud**: Free tier available
- **Upstash**: Serverless Redis

### Verify Redis Connection

```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # Should return True
```

---

## Step 2: Install Dependencies

Update `backend/requirements.txt`:

```txt
# Existing dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-docx==1.1.0
PyPDF2==3.0.1
openai==1.3.0
pydantic==2.5.0
python-dotenv==1.0.0
email-validator==2.1.0
firebase-admin==7.1.0
mangum==0.17.0

# New dependencies for scalability
celery==5.3.4
redis==5.0.1
slowapi==0.1.9
aiosmtplib==3.0.1
httpx==0.25.2  # For async HTTP requests
```

Install:
```bash
cd backend
pip install -r requirements.txt
```

---

## Step 3: Create Celery Configuration

### File: `backend/celery_app.py`

```python
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'resume_processor',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.tasks.resume_tasks', 'backend.tasks.email_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    'backend.tasks.resume_tasks.*': {'queue': 'resume_processing'},
    'backend.tasks.email_tasks.*': {'queue': 'email_sending'},
}
```

---

## Step 4: Create Async GPT Service

### File: `backend/services/gpt_service.py`

```python
import openai
import os
from typing import Dict, Any, List
import asyncio
from openai import AsyncOpenAI

class GPTService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
    
    async def analyze_resume_async(
        self, 
        resume_text: str, 
        job_description: str
    ) -> Dict[str, Any]:
        """Analyze resume using GPT-4o mini asynchronously"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert HR recruiter. Analyze the resume against the job description and provide:
1. A score from 0-10 (10 being perfect match)
2. A brief explanation of why the candidate was/wasn't shortlisted
3. Key strengths and weaknesses

Return your response in this exact JSON format:
{
    "score": 7.5,
    "explanation": "Brief explanation of the decision",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"]
}"""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:
{job_description}

Resume:
{resume_text[:3000]}

Analyze this resume against the job description and provide your assessment."""
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            import json
            analysis = json.loads(result)
            
            return {
                "score": float(analysis.get("score", 0)),
                "explanation": analysis.get("explanation", "No explanation provided"),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", [])
            }
        except Exception as e:
            print(f"Error in GPT analysis: {e}")
            return {
                "score": 0.0,
                "explanation": "Error occurred during analysis",
                "strengths": [],
                "weaknesses": []
            }
    
    async def analyze_resumes_batch(
        self,
        resumes: List[Dict[str, str]],
        job_description: str,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Analyze multiple resumes in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(resume_data: Dict[str, str]):
            async with semaphore:
                return await self.analyze_resume_async(
                    resume_data['text'],
                    job_description
                )
        
        tasks = [analyze_with_limit(resume) for resume in resumes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing resume {i}: {result}")
                processed_results.append({
                    "score": 0.0,
                    "explanation": f"Error: {str(result)}",
                    "strengths": [],
                    "weaknesses": []
                })
            else:
                processed_results.append(result)
        
        return processed_results

# Global instance
gpt_service = GPTService()
```

---

## Step 5: Create Resume Processing Tasks

### File: `backend/tasks/__init__.py`

```python
# Empty init file
```

### File: `backend/tasks/resume_tasks.py`

```python
from celery import Task
from backend.celery_app import celery_app
from backend.services.gpt_service import gpt_service
from backend.firebase_service import firebase_service
from backend.s3_service import s3_service
from typing import List, Dict, Any
import tempfile
import os
from datetime import datetime

# Import text extraction functions
from backend.main import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_email_from_text,
    extract_name_from_text,
    extract_phone_from_text,
    validate_extracted_data,
    categorize_resume
)

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
        resume_files_data: List of dicts with 'filename', 'content' (bytes), 'file_type'
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
    
    for resume_data in resume_files_data:
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
            
            # Extract text
            content = resume_data['content']
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
                if user_id:
                    try:
                        s3_url = s3_service.upload_resume_from_bytes(
                            content,
                            user_id,
                            filename
                        )
                    except Exception as e:
                        print(f"S3 upload failed: {e}")
                
                # Analyze with GPT (async)
                import asyncio
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
                
                results[category].append(resume_result)
                
                # Store in Firebase if user_id provided
                if user_id:
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
                    except Exception as e:
                        print(f"Firebase storage failed: {e}")
                
                processed += 1
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"Error processing resume: {e}")
            # Add fallback entry
            results["rejected"].append({
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
            })
            processed += 1
    
    return {
        "data": results,
        "metadata": {
            "total_processed": processed,
            "processed_at": datetime.now().isoformat(),
            "user_id": user_id
        }
    }
```

---

## Step 6: Update Main API Endpoint

### Modify `backend/main.py` - Process Endpoint

Replace the existing `/process` endpoint with:

```python
from backend.tasks.resume_tasks import process_resume_batch
from celery.result import AsyncResult

@app.post("/process")
async def process_resumes(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(None),
    job_description_file: UploadFile = File(None),
    user_id: str = Form(None)
):
    """Process uploaded resumes asynchronously"""
    try:
        # Check token balance
        if user_id:
            tokens_needed = calculate_tokens_needed(len(resumes))
            user_tokens = get_user_tokens(user_id)
            
            if user_tokens['tokens'] < tokens_needed:
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient tokens. You need {tokens_needed} tokens but only have {user_tokens['tokens']}."
                )
        
        # Process job description
        final_job_description = job_description
        if job_description_file:
            jd_content = await job_description_file.read()
            # ... (existing JD processing logic)
        
        if not final_job_description:
            raise HTTPException(status_code=400, detail="No job description provided")
        
        # Prepare resume files data
        resume_files_data = []
        for resume_file in resumes:
            content = await resume_file.read()
            file_extension = resume_file.filename.split('.')[-1].lower()
            
            resume_files_data.append({
                'filename': resume_file.filename,
                'content': content,
                'file_type': file_extension
            })
        
        # Start background task
        task = process_resume_batch.delay(
            resume_files_data,
            final_job_description,
            user_id
        )
        
        # Deduct tokens
        if user_id:
            tokens_used = calculate_tokens_needed(len(resumes))
            use_tokens(user_id, tokens_used, "resume_screening")
        
        return {
            "message": "Resume processing started",
            "task_id": task.id,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process/status/{task_id}")
async def get_process_status(task_id: str):
    """Get status of resume processing task"""
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Task is waiting to be processed'
        }
    elif task_result.state == 'PROGRESS':
        response = {
            'state': task_result.state,
            'current': task_result.info.get('current', 0),
            'total': task_result.info.get('total', 1),
            'status': task_result.info.get('status', '')
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'state': task_result.state,
            'result': task_result.result
        }
    else:  # FAILURE
        response = {
            'state': task_result.state,
            'error': str(task_result.info)
        }
    
    return response
```

---

## Step 7: Add Rate Limiting

### File: `backend/middleware/rate_limit.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
```

### Update `backend/main.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.middleware.rate_limit import limiter

# Add limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to endpoints
@app.post("/process")
@limiter.limit("10/minute")  # 10 requests per minute
async def process_resumes(request: Request, ...):
    # ... existing code

@app.post("/send-personalized-emails")
@limiter.limit("20/minute")
async def send_personalized_emails(request: Request, ...):
    # ... existing code
```

---

## Step 8: Create Cache Service

### File: `backend/services/cache_service.py`

```python
import redis
import json
import hashlib
import os
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

class CacheService:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = 3600  # 1 hour
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments"""
        key_string = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        # Hash long keys
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        return key_string
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def get_gpt_analysis_cache_key(self, resume_text: str, job_description: str) -> str:
        """Generate cache key for GPT analysis"""
        # Use hash of resume text and job description
        content_hash = hashlib.md5(
            f"{resume_text[:1000]}:{job_description[:500]}".encode()
        ).hexdigest()
        return self._generate_key("gpt_analysis", content_hash)

# Global instance
cache_service = CacheService()
```

---

## Step 9: Update Environment Variables

### Update `backend/env.example`

```env
# Existing variables
OPENAI_API_KEY=your_openai_api_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# New variables for scalability
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600
```

---

## Step 10: Update Docker Compose

### Update `docker-compose.yml`

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery_worker:
    build: ./backend
    command: celery -A backend.celery_app worker --loglevel=info --queues=resume_processing,email_sending
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FIREBASE_SERVICE_ACCOUNT_KEY=${FIREBASE_SERVICE_ACCOUNT_KEY}
    depends_on:
      - redis
      - backend

  celery_beat:
    build: ./backend
    command: celery -A backend.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      # ... other env vars
    depends_on:
      - redis
    volumes:
      - ./backend:/app

  frontend:
    # ... existing frontend config

volumes:
  redis_data:
```

---

## Step 11: Update Frontend for Async Processing

### Update `frontend/src/services/api.ts`

Add new functions:

```typescript
export const processResumesAsync = async (formData: FormData) => {
  const response = await api.post('/process', formData);
  return response.data; // Returns { task_id, status }
};

export const getProcessStatus = async (taskId: string) => {
  const response = await api.get(`/process/status/${taskId}`);
  return response.data;
};
```

### Update Upload Page to Poll for Status

```typescript
const pollTaskStatus = async (taskId: string) => {
  const interval = setInterval(async () => {
    const status = await getProcessStatus(taskId);
    
    if (status.state === 'SUCCESS') {
      clearInterval(interval);
      // Handle success
      setResults(status.result);
    } else if (status.state === 'FAILURE') {
      clearInterval(interval);
      // Handle error
      setError(status.error);
    } else if (status.state === 'PROGRESS') {
      // Update progress
      setProgress({
        current: status.current,
        total: status.total,
        status: status.status
      });
    }
  }, 2000); // Poll every 2 seconds
};
```

---

## Step 12: Testing

### Test Async Processing

```python
# test_async_processing.py
import requests
import time

# Upload resumes
files = [('resumes', open('resume1.pdf', 'rb')), ...]
data = {'job_description': '...', 'user_id': '...'}

response = requests.post('http://localhost:8000/process', files=files, data=data)
task_id = response.json()['task_id']

# Poll for status
while True:
    status = requests.get(f'http://localhost:8000/process/status/{task_id}').json()
    print(status)
    
    if status['state'] == 'SUCCESS':
        print("Done!", status['result'])
        break
    elif status['state'] == 'FAILURE':
        print("Error!", status['error'])
        break
    
    time.sleep(2)
```

---

## Step 13: Run Celery Worker

```bash
# Start Redis
redis-server

# Start Celery worker
cd backend
celery -A backend.celery_app worker --loglevel=info

# In another terminal, start FastAPI
uvicorn main:app --reload
```

---

## Verification Checklist

- [ ] Redis is running and accessible
- [ ] Celery worker is running
- [ ] Can submit resume processing job
- [ ] Can poll for job status
- [ ] Rate limiting is working
- [ ] Caching is working
- [ ] Multiple resumes process in parallel
- [ ] Frontend polls for status correctly

---

## Next Steps

After completing Phase 1:
1. Monitor performance improvements
2. Collect metrics
3. Move to Phase 2 (Optimization)

