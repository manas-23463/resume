# 🚨 Deployment Fixes Required

## **Backend Deployment Issues & Fixes**

### **Problem 1: Vercel Configuration**
- **Issue**: Backend not properly configured for Vercel serverless functions
- **Fix**: Updated `vercel.json` to use `api/index.py` as entry point

### **Problem 2: CORS Configuration**
- **Issue**: Frontend domains not allowed in CORS
- **Fix**: Added your specific Vercel domains to CORS origins

### **Problem 3: Environment Variables**
- **Issue**: Firebase service account not properly configured
- **Fix**: Set as environment variable instead of file

## **Required Environment Variables for Backend**

Set these in your Vercel backend project:

| Variable | Value | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `your_openai_key` | OpenAI API key |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | `{"type":"service_account",...}` | Full Firebase JSON |
| `FIREBASE_PROJECT_ID` | `resume-screener-84800` | Firebase project ID |
| `SMTP_SERVER` | `email-smtp.us-east-1.amazonaws.com` | Email server |
| `SMTP_PORT` | `587` | Email port |
| `EMAIL_USER` | `your_email_user` | Email username |
| `EMAIL_PASSWORD` | `your_email_password` | Email password |

## **Required Environment Variables for Frontend**

Set these in your Vercel frontend project:

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | `https://your-backend.vercel.app` | Backend API URL |

## **Steps to Fix Deployment**

### **1. Update Backend Repository**
```bash
cd /path/to/your/backend/repo
git add .
git commit -m "Fix Vercel deployment configuration"
git push origin main
```

### **2. Redeploy Backend**
- Go to your backend Vercel project
- Click "Redeploy" or it will auto-deploy from the updated code

### **3. Update Frontend Environment Variables**
- Go to your frontend Vercel project
- Settings > Environment Variables
- Set `VITE_API_URL` to your backend URL (e.g., `https://your-backend.vercel.app`)

### **4. Redeploy Frontend**
- Go to your frontend Vercel project
- Click "Redeploy" or it will auto-deploy

## **Testing the Fix**

1. **Test Backend**: Visit `https://your-backend.vercel.app/docs` - should show FastAPI docs
2. **Test Frontend**: Visit your frontend URL - should load without errors
3. **Test Login**: Try logging in - should work if backend is properly configured

## **Common Issues & Solutions**

### **Issue**: "Failed to log in: Login failed"
**Solution**: 
- Check if backend is running: `https://your-backend.vercel.app/docs`
- Verify `VITE_API_URL` is set correctly in frontend
- Check backend logs for errors

### **Issue**: CORS errors in browser console
**Solution**:
- Verify your frontend domain is in backend CORS origins
- Redeploy backend after CORS changes

### **Issue**: Firebase authentication errors
**Solution**:
- Verify `FIREBASE_SERVICE_ACCOUNT_KEY` is set as environment variable
- Check Firebase project ID is correct
- Ensure Firebase project has Firestore enabled
