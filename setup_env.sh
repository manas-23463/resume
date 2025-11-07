#!/bin/bash

echo "🔧 Setting up environment file for Resume Shortlisting System"
echo "=============================================================="

# Check if .env file already exists
if [ -f "backend/.env" ]; then
    echo "⚠️  .env file already exists in backend directory"
    echo "Do you want to overwrite it? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
fi

# Create .env file
echo "📝 Creating .env file..."
cat > backend/.env << EOF
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
EMAIL_USER=your_aws_access_key_here
EMAIL_PASSWORD=your_aws_secret_key_here
EOF

echo "✅ .env file created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update the OPENAI_API_KEY in backend/.env with your actual OpenAI API key"
echo "2. Restart your backend server"
echo "3. Try sending emails again"
echo ""
echo "🔍 To check if the .env file is being loaded correctly, look for these messages in your backend logs:"
echo "   - 'Email configuration missing' (if .env is not loaded)"
echo "   - 'Using SMTP server: email-smtp.us-east-1.amazonaws.com:587' (if working)"
echo ""
echo "🚀 Your email system should now work with personalized emails!"

