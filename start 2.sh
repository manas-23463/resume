#!/bin/bash

echo "🚀 Starting Resume Shortlisting System..."

# Check if .env file exists in backend
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Please create backend/.env file with your API keys"
    echo "   Copy backend/env.example to backend/.env and fill in your credentials"
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
cd ../frontend
# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo "✅ Application started!"
echo "   Frontend: http://localhost:5173"
echo "   Backend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait

# Cleanup
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
