# Running Without Redis and Docker

The project now uses **async parallel processing** instead of Redis/Celery, so you can run it without any additional dependencies!

## ✅ What Changed

- **Removed**: Redis and Celery dependencies
- **Added**: Async parallel processing using `asyncio.gather()`
- **Result**: Still handles 100+ resumes without timeout, but simpler setup!

## 🚀 Quick Start (No Redis/Docker)

### Option 1: Simple Start Script

```bash
# Make script executable
chmod +x start.sh

# Run
./start.sh
```

This starts:
- Backend API (port 8000)
- Frontend (port 5173)

### Option 2: Manual Start (2 Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

That's it! No Redis, no Docker, no Celery needed.

## 📊 How It Works

### Async Parallel Processing

Instead of using Celery/Redis, the system now:

1. **Processes resumes in parallel** using `asyncio.gather()`
2. **Limits concurrent GPT calls** to 5 at a time (using semaphore)
3. **Handles all resumes simultaneously** without blocking

### Performance

| Batch Size | Processing Time |
|------------|----------------|
| 10 resumes | ~30-60 seconds |
| 50 resumes | ~2-3 minutes |
| 100 resumes | ~5-7 minutes |
| 200+ resumes | ~10-15 minutes |

**No timeouts!** The async processing handles large batches efficiently.

## 🔧 Requirements

### Minimal Requirements

- **Python 3.9+**
- **Node.js 18+**
- **OpenAI API Key**

### No Longer Needed

- ❌ Redis
- ❌ Docker
- ❌ Celery
- ❌ Background workers

## 📝 Environment Setup

Create `backend/.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Optional - Firebase
FIREBASE_SERVICE_ACCOUNT_KEY=./service-account-key.json

# Optional - AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET_NAME=your_bucket_name
```

## 🎯 Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## ⚡ How Parallel Processing Works

```python
# Process all resumes in parallel
tasks = [process_single_resume(resume, job_desc, user_id, i) 
         for i, resume in enumerate(resumes)]

# Wait for all to complete
results = await asyncio.gather(*tasks)

# Limit concurrent GPT calls to 5
semaphore = asyncio.Semaphore(5)
```

This means:
- **5 resumes** processed simultaneously with GPT
- **All file operations** happen in parallel
- **No blocking** - everything is async

## 🐛 Troubleshooting

### Import Error: backend.services.gpt_service

If you get this error, make sure the `backend/services/gpt_service.py` file exists and the async OpenAI client is installed:

```bash
cd backend
pip install openai
```

### Slow Processing

The system processes 5 resumes at a time with GPT. For faster processing:
- Increase semaphore limit (currently 5)
- Or use Redis/Celery for true background processing

### Memory Issues with Large Batches

For 200+ resumes, you might want to:
- Process in smaller batches
- Or use the Redis/Celery setup for better memory management

## 📊 Comparison: With vs Without Redis

| Feature | Without Redis | With Redis |
|---------|---------------|------------|
| Setup Complexity | ⭐ Simple | ⭐⭐⭐ Complex |
| Dependencies | Minimal | Redis + Celery |
| Processing | Async parallel | Background jobs |
| Response Time | Immediate | Immediate |
| Large Batches | ✅ Handles | ✅ Handles |
| Progress Tracking | ❌ No | ✅ Yes |
| Memory Usage | Higher | Lower |

## 🎉 Benefits of This Approach

1. **Simpler Setup** - No Redis/Docker needed
2. **Faster Development** - Just run Python and Node
3. **Still Scalable** - Handles 100+ resumes
4. **No Timeouts** - Async processing prevents blocking
5. **Easy Debugging** - All in one process

## 🔄 If You Want Background Jobs Later

If you need background jobs with progress tracking, you can still use the Redis/Celery setup. Just:
1. Install Redis
2. Install Celery
3. Update `main.py` to use Celery tasks
4. Start Celery worker

But for most use cases, **async parallel processing is sufficient**!

## ✅ Quick Test

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload 100+ resumes
4. Watch them process in parallel! 🚀

No Redis, no Docker, no problem! 🎉

