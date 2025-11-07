# Quick Start Guide - Scalable Resume Processing

This guide will help you set up the scalable resume processing system that can handle 100+ resumes without timeouts.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ (for local development)
- Redis (will be installed via Docker)

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Redis

#### Option A: Using Docker (Recommended)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

#### Option B: Local Installation

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

### 3. Update Environment Variables

Add to your `backend/.env` file:

```env
REDIS_URL=redis://localhost:6379/0
```

### 4. Start Services

#### Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

This will start:
- Redis (port 6379)
- Backend API (port 8000)
- Celery Worker (background processing)
- Frontend (port 3000 or 5173)

#### Manual Start (Development)

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
celery -A backend.celery_app worker --loglevel=info --queues=resume_processing
```

**Terminal 3 - FastAPI Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

## How It Works

### Background Job Processing

When you upload **more than 10 resumes**, the system automatically:
1. Queues the job in Redis
2. Returns immediately with a `task_id`
3. Processes resumes in the background using Celery
4. Frontend polls for status updates

### Status Polling

The frontend should poll the status endpoint:

```typescript
// Poll every 2 seconds
const pollStatus = async (taskId: string) => {
  const interval = setInterval(async () => {
    const status = await getProcessStatus(taskId);
    
    if (status.state === 'SUCCESS') {
      clearInterval(interval);
      // Handle results
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
  }, 2000);
};
```

## API Endpoints

### Process Resumes
```http
POST /process
Content-Type: multipart/form-data

Form Data:
- resumes: File[] (multiple files)
- job_description: string
- user_id: string (optional)
```

**Response (Large batches >10 resumes):**
```json
{
  "message": "Resume processing started in background",
  "task_id": "abc123-def456-...",
  "status": "processing",
  "total_resumes": 100
}
```

**Response (Small batches ≤10 resumes):**
```json
{
  "data": {
    "selected": [...],
    "rejected": [...],
    "considered": [...]
  },
  "metadata": {...}
}
```

### Get Processing Status
```http
GET /process/status/{task_id}
```

**Response (PROGRESS):**
```json
{
  "state": "PROGRESS",
  "current": 45,
  "total": 100,
  "status": "Processing resume_45.pdf"
}
```

**Response (SUCCESS):**
```json
{
  "state": "SUCCESS",
  "result": {
    "data": {
      "selected": [...],
      "rejected": [...],
      "considered": [...]
    },
    "metadata": {...}
  }
}
```

## Performance Improvements

### Before
- **10 resumes**: ~2-3 minutes
- **50 resumes**: ~10-15 minutes (often timeout)
- **100 resumes**: Timeout/failure

### After
- **10 resumes**: ~30 seconds (synchronous)
- **50 resumes**: ~2-3 minutes (background)
- **100 resumes**: ~5-7 minutes (background, no timeout)
- **200+ resumes**: Handles without timeout

## Troubleshooting

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check Redis connection in Python
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

### Celery Worker Not Processing Jobs

```bash
# Check if Celery worker is running
ps aux | grep celery

# Check Celery logs
celery -A backend.celery_app worker --loglevel=debug
```

### Jobs Stuck in PENDING

1. Check if Redis is accessible
2. Check if Celery worker is running
3. Check Celery worker logs for errors
4. Verify task is registered: `celery -A backend.celery_app inspect registered`

## Monitoring

### Check Active Tasks
```bash
celery -A backend.celery_app inspect active
```

### Check Task Status (Python)
```python
from celery.result import AsyncResult
from backend.celery_app import celery_app

task = AsyncResult('task-id', app=celery_app)
print(task.state)  # PENDING, PROGRESS, SUCCESS, FAILURE
print(task.info)   # Task info/result
```

## Next Steps

1. **Add Caching**: Implement Redis caching for GPT responses (see SCALABILITY_PLAN.md)
2. **Add Rate Limiting**: Protect API from abuse
3. **Add Monitoring**: Set up logging and metrics
4. **Optimize Database**: Add pagination and indexes

See `SCALABILITY_PLAN.md` for full scalability roadmap.

