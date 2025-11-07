# Commands to Run the Project

## ✅ Simple Setup (Recommended - No Redis/Docker Needed!)

The project now uses **async parallel processing** - no Redis or Docker required!

### Quick Start (2 Terminals)

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

That's it! The system processes resumes in parallel using async/await.

### Or Use Start Script

```bash
chmod +x start.sh
./start.sh
```

---

## 🐳 Option 1: Docker Compose (Optional)

If you prefer Docker, this starts everything in one command: Redis, Celery Worker, Backend, and Frontend.

### Prerequisites
- Docker and Docker Compose installed
- `.env` file configured in `backend/` directory

### Command
```bash
# From project root directory
docker-compose up --build
```

### To run in background (detached mode)
```bash
docker-compose up -d --build
```

### To stop
```bash
docker-compose down
```

### To view logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery_worker
docker-compose logs -f backend
docker-compose logs -f redis
```

### Access Points
- **Frontend**: http://localhost:3000 (production) or http://localhost:5173 (dev)
- **Backend API**: http://localhost:8000
- **Redis**: localhost:6379

---

## 💻 Option 2: Manual Setup (Development)

For development, you can run services manually in separate terminals.

### Prerequisites
- Python 3.9+
- Node.js 18+
- Redis installed and running

### Step 1: Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### Step 2: Start Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Or using Docker:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Step 3: Start Services (4 Terminals)

**Terminal 1 - Redis (if not using Docker):**
```bash
redis-server
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
celery -A backend.celery_app worker --loglevel=info --queues=resume_processing
```

**Terminal 3 - Backend API:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access Points
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🚀 Option 3: Using Start Script (Without Redis/Celery)

For quick testing without background processing (small batches only):

```bash
# Make script executable
chmod +x start.sh

# Run
./start.sh
```

**Note**: This doesn't include Redis/Celery, so it will only handle small batches (≤10 resumes) synchronously.

---

## 📋 Quick Reference

### Docker Compose Commands

```bash
# Start all services
docker-compose up --build

# Start in background
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart celery_worker

# Rebuild a specific service
docker-compose up --build celery_worker
```

### Manual Commands

```bash
# Start Redis
redis-server

# Start Celery Worker
cd backend
celery -A backend.celery_app worker --loglevel=info

# Start Backend
cd backend
uvicorn main:app --reload

# Start Frontend
cd frontend
npm run dev
```

### Verification Commands

```bash
# Check Redis
redis-cli ping

# Check Celery workers
celery -A backend.celery_app inspect active

# Check Celery registered tasks
celery -A backend.celery_app inspect registered

# Test backend API
curl http://localhost:8000/
```

---

## ⚙️ Environment Setup

### Required Environment Variables

Create `backend/.env` file:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Redis (for background processing)
REDIS_URL=redis://localhost:6379/0

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Firebase (optional)
FIREBASE_SERVICE_ACCOUNT_KEY=./service-account-key.json

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET_NAME=your_bucket_name
```

---

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# Check Redis port
netstat -an | grep 6379
```

### Celery Worker Not Processing
```bash
# Check if worker is running
ps aux | grep celery

# Check worker logs
celery -A backend.celery_app worker --loglevel=debug

# Check active tasks
celery -A backend.celery_app inspect active
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Docker Issues
```bash
# Remove all containers
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Check container status
docker-compose ps
```

---

## 📝 Recommended Setup

**For Production/Testing:**
```bash
docker-compose up --build
```

**For Development:**
Use manual setup (Option 2) for better debugging and hot-reload.

---

## ✅ Quick Start Checklist

- [ ] Docker installed (for Docker Compose) OR Redis installed (for manual)
- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] `backend/.env` file created with API keys
- [ ] Dependencies installed (`pip install -r requirements.txt` and `npm install`)
- [ ] Redis running (if manual setup)
- [ ] All services started

---

## 🎯 What Happens When You Run

1. **Redis** starts (message broker for Celery)
2. **Celery Worker** starts (processes background jobs)
3. **Backend API** starts (FastAPI server on port 8000)
4. **Frontend** starts (React app on port 5173 or 3000)

When you upload **>10 resumes**:
- Job is queued in Redis
- Celery worker processes it in background
- API returns immediately with `task_id`
- Frontend polls for status updates

