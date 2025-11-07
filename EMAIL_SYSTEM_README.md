# Personalized Email System

## Overview

The personalized email system automatically generates and sends customized emails to candidates using data extracted from both the job description and candidate resumes. This eliminates the need for manual email templates with variables.

## Features

### ✨ **Automatic Data Extraction**
- **From Job Description**: Company name, position title, department, location, key skills
- **From Resume**: Candidate name, email, phone, strengths, weaknesses, score

### 📧 **Personalized Email Generation**
- Uses GPT-4o mini to create unique emails for each candidate
- Incorporates specific details from both JD and resume
- Different templates for: Selected, Considered, Rejected candidates

### 🔧 **SMTP Configuration**
- Configured with AWS SES credentials
- Server: `email-smtp.us-east-1.amazonaws.com`
- Port: 587
- Authentication: SMTP credentials provided

## How It Works

### 1. **Data Extraction Process**
```
Job Description → GPT Analysis → Company Info
Resume Content → GPT Analysis → Candidate Info
```

### 2. **Email Generation**
```
Company Info + Candidate Info + Category → GPT → Personalized Email
```

### 3. **Email Sending**
```
Personalized Email → SMTP Server → Candidate's Inbox
```

## API Endpoints

### Generate Personalized Emails
```http
POST /generate-personalized-emails
Content-Type: application/json

{
  "job_description": "Software Engineer at TechCorp...",
  "resumes": [
    {
      "name": "John Smith",
      "email": "john@example.com",
      "score": 8.5,
      "strengths": ["Python", "React"],
      "weaknesses": ["Limited leadership"]
    }
  ],
  "category": "selected"
}
```

### Send Personalized Emails
```http
POST /send-personalized-emails
Content-Type: application/json

{
  "job_description": "Software Engineer at TechCorp...",
  "resumes": [...],
  "category": "selected"
}
```

## Frontend Integration

### EmailModal Component
- Shows personalized email notice when job description is available
- Automatically uses personalized emails when JD is present
- Falls back to generic templates when no JD is provided

### ResultsPage Integration
- Detects if job description is available
- Automatically switches to personalized email mode
- Shows success message for personalized emails

## Example Email Output

### Before (Generic Template)
```
Subject: Application Status Update

Dear Candidate,

Thank you for your interest in the Position at Our Company...
```

### After (Personalized)
```
Subject: Congratulations - You've Been Selected for the Next Round

Dear John Smith,

I hope this message finds you well.

Thank you for your interest in the Software Engineer position at TechCorp Inc. We are pleased to inform you that your application has been reviewed, and we are considering you for the next steps in our recruitment process.

Your qualifications in Python, React, and AWS have impressed our team, and we believe you would be a valuable addition to our Engineering department in San Francisco.

You may be contacted soon for further discussions or to schedule an interview. We appreciate your patience as we continue our evaluation process.

Thank you once again for your interest in joining our team. We look forward to the possibility of working together.

Best regards,
HR Team
TechCorp Inc.
```

## Configuration

### Environment Variables
```bash
# SMTP Configuration
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
EMAIL_USER=your_aws_access_key_here
EMAIL_PASSWORD=your_aws_secret_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

## Testing

Run the test script to verify the email system:
```bash
python test_email_system.py
```

## Benefits

1. **No More Variables**: Emails are fully personalized using real data
2. **Professional Quality**: GPT-generated content is natural and professional
3. **Time Saving**: No need to manually create email templates
4. **Consistent Branding**: All emails maintain company voice and tone
5. **Scalable**: Works with any number of candidates and job descriptions

## Error Handling

- **Fallback Templates**: If GPT fails, system uses basic templates
- **Email Validation**: Invalid email addresses are skipped with error logging
- **SMTP Errors**: Failed emails are logged with specific error messages
- **Rate Limiting**: Built-in delays to prevent SMTP server overload

## Security

- SMTP credentials are stored in environment variables
- No sensitive data is logged in plain text
- Email content is generated server-side for security
- All API endpoints require proper authentication

## Future Enhancements

- [ ] Email templates customization
- [ ] Multi-language support
- [ ] Email scheduling
- [ ] Email tracking and analytics
- [ ] Custom sender names and signatures

