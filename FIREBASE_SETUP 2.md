# Firebase Authentication & Data Storage Setup

This document explains how to set up Firebase Authentication and Firestore for the Resume Shortlisting System.

## Prerequisites

1. A Google account
2. Node.js 18+ and npm
3. Python 3.9+

## Firebase Project Setup

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter project name (e.g., "resume-shortlisting")
4. Enable Google Analytics (optional)
5. Click "Create project"

### 2. Enable Authentication

1. In the Firebase Console, go to "Authentication" → "Sign-in method"
2. Enable "Email/Password" provider
3. Enable "Phone" provider (optional, for phone number authentication)
4. Configure any additional settings as needed

### 3. Create Firestore Database

1. Go to "Firestore Database" in the Firebase Console
2. Click "Create database"
3. Choose "Start in test mode" (for development)
4. Select a location for your database
5. Click "Done"

### 4. Get Firebase Configuration

1. Go to Project Settings (gear icon) → "General"
2. Scroll down to "Your apps" section
3. Click "Add app" → Web app (</>) icon
4. Register your app with a nickname
5. Copy the Firebase configuration object

## Environment Configuration

### Frontend Environment Variables

Create a `.env` file in the `frontend` directory:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=your_app_id

# API Configuration
VITE_API_URL=http://localhost:8000
```

### Backend Environment Variables

Create a `.env` file in the `backend` directory:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Firebase Configuration (for backend)
FIREBASE_SERVICE_ACCOUNT_KEY=path/to/your/service-account-key.json
# OR set GOOGLE_APPLICATION_CREDENTIALS environment variable
# GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

## Firebase Service Account Setup (Backend)

### 1. Generate Service Account Key

1. Go to Firebase Console → Project Settings → "Service accounts"
2. Click "Generate new private key"
3. Download the JSON file
4. Place it in your backend directory (e.g., `backend/service-account-key.json`)

### 2. Update Environment Variables

Set the path to your service account key in the backend `.env` file:

```env
FIREBASE_SERVICE_ACCOUNT_KEY=./service-account-key.json
```

## Firestore Security Rules

Update your Firestore security rules to allow authenticated users to read/write their own data:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own profile
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Users can read/write their own resume data
    match /resumeData/{document} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.userId;
    }
  }
}
```

## Data Structure

### User Profile Document (`/users/{userId}`)

```json
{
  "uid": "user_id",
  "email": "user@example.com",
  "phoneNumber": "+1234567890",
  "displayName": "John Doe",
  "createdAt": "2024-01-01T00:00:00Z",
  "lastLoginAt": "2024-01-01T00:00:00Z"
}
```

### Resume Data Document (`/resumeData/{documentId}`)

```json
{
  "id": "document_id",
  "userId": "user_id",
  "candidateName": "Jane Smith",
  "candidateEmail": "jane@example.com",
  "candidatePhone": "+1234567890",
  "fileName": "resume.pdf",
  "category": "selected",
  "score": 8.5,
  "content": "resume text content",
  "explanation": "AI explanation",
  "strengths": ["skill1", "skill2"],
  "weaknesses": ["area1", "area2"],
  "extractedAt": "2024-01-01T00:00:00Z"
}
```

## Features Implemented

### Authentication
- ✅ Email/Password authentication
- ✅ User registration with profile data
- ✅ Phone number authentication (optional)
- ✅ Protected routes
- ✅ User session management

### Data Storage
- ✅ User profile storage (email, phone, display name)
- ✅ Resume data storage (candidate info, scores, categories)
- ✅ Automatic data extraction and storage
- ✅ User-specific data isolation

### Dashboard
- ✅ User profile display
- ✅ Resume processing statistics
- ✅ Historical resume data
- ✅ Data visualization

## Usage

### 1. Start the Application

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

### 2. Access the Application

1. Navigate to `http://localhost:5173`
2. You'll be redirected to the authentication page
3. Create an account or sign in
4. Upload and process resumes
5. View your data in the dashboard

### 3. User Flow

1. **Authentication**: Users must sign up/sign in to access the application
2. **Resume Upload**: Upload resumes with job descriptions
3. **Processing**: Resumes are processed and categorized
4. **Data Storage**: All data is automatically stored in Firestore
5. **Dashboard**: View statistics and historical data

## Troubleshooting

### Common Issues

1. **Firebase Configuration Error**
   - Verify all environment variables are set correctly
   - Check Firebase project settings

2. **Authentication Issues**
   - Ensure Authentication is enabled in Firebase Console
   - Check if email/password provider is enabled

3. **Firestore Permission Denied**
   - Update security rules
   - Verify user authentication status

4. **Service Account Issues**
   - Ensure service account key is valid
   - Check file path in environment variables

### Debug Mode

Enable debug logging by setting:

```env
# Frontend
VITE_DEBUG=true

# Backend
DEBUG=true
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **Service Account**: Keep service account keys secure
3. **Firestore Rules**: Implement proper security rules
4. **API Keys**: Rotate API keys regularly

## Production Deployment

### Environment Variables

Set the following environment variables in your production environment:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
- `FIREBASE_SERVICE_ACCOUNT_KEY`

### Security Rules

Update Firestore security rules for production:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == userId &&
        request.auth.token.email_verified == true;
    }
    
    match /resumeData/{document} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.userId &&
        request.auth.token.email_verified == true;
    }
  }
}
```

## Support

For issues or questions:
1. Check the Firebase Console for errors
2. Review browser console for frontend errors
3. Check backend logs for API errors
4. Verify all environment variables are set correctly
