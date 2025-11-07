#!/bin/bash

echo "🔧 Setting up Resume Shortlisting System..."

# Create .env file from example if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env file..."
    cp backend/env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys"
    echo "   - EMAIL_USER: Your Gmail address"
    echo "   - EMAIL_PASSWORD: Your Gmail app password"
    echo ""
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd ../frontend
# Clean install to ensure compatibility
rm -rf node_modules package-lock.json
npm install

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your API keys"
echo "2. Run ./start.sh to start the application"
echo "3. Or use docker-compose up for Docker deployment"
