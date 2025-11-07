# Vercel Backend Deployment Guide

## Environment Variables Required

Set these in your Vercel dashboard under Settings > Environment Variables:

### Required Variables:
```
OPENAI_API_KEY=your_openai_api_key_here
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
FIREBASE_PROJECT_ID=resume-screener-84800
```

### Optional Variables:
```
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
EMAIL_USER=your_email_user
EMAIL_PASSWORD=your_email_password
```

## Firebase Service Account Setup

1. Go to Firebase Console > Project Settings > Service Accounts
2. Generate new private key
3. Copy the entire JSON content
4. Set as `FIREBASE_SERVICE_ACCOUNT_KEY` environment variable in Vercel

## Deployment Steps

1. Connect your GitHub repository to Vercel
2. Set the root directory to `backend`
3. Add all environment variables
4. Deploy!

## Important Notes

- File uploads may have size limits on Vercel (50MB max)
- Consider using S3 for large file storage
- Firebase service account key must be set as environment variable, not file
