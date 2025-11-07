from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv
import openai
from pydantic import BaseModel
import re
import base64
import asyncio

# Load environment variables first
load_dotenv()

# Firebase service is required for authentication
try:
    from firebase_service import firebase_service
    FIREBASE_AVAILABLE = True
except Exception as e:
    print(f"Firebase service not available: {e}")
    FIREBASE_AVAILABLE = False

# S3 service for resume storage
try:
    from s3_service import s3_service
    S3_AVAILABLE = True
except Exception as e:
    print(f"S3 service not available: {e}")
    S3_AVAILABLE = False

# Async GPT service for parallel processing
try:
    from backend.services.gpt_service import gpt_service
    ASYNC_GPT_AVAILABLE = True
except Exception as e:
    print(f"Async GPT service not available: {e}")
    ASYNC_GPT_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(title="Resume Shortlisting API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "https://resume-screener-mu.vercel.app",  # Your frontend domain
        "https://resume-screener-tgk6.vercel.app",  # Your frontend domain
        "https://*.vercel.app",  # Allow all Vercel domains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# GPT-4o mini configuration
GPT_MODEL = "gpt-4o-mini"

# Pydantic models
class EmailRequest(BaseModel):
    category: str
    resumes: List[Dict[str, Any]]
    emailContent: str

class EmailResponse(BaseModel):
    message: str
    sent_count: int

class ResumeDataRequest(BaseModel):
    user_id: str
    resume_data: List[Dict[str, Any]]

class ResumeDataResponse(BaseModel):
    message: str
    stored_count: int

class AuthRequest(BaseModel):
    email: str
    password: str
    displayName: str = None
    phoneNumber: str = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    user_profile: Optional[dict] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenBalance(BaseModel):
    user_id: str
    tokens: int
    total_used: int
    created_at: str
    updated_at: str

class TokenUsage(BaseModel):
    user_id: str
    tokens_used: int
    operation: str  # 'resume_screening', 'email_generation', etc.
    created_at: str

class PurchaseTokens(BaseModel):
    user_id: str
    token_package: str  # 'small', 'medium', 'large'
    payment_method: str

# Token management functions
def initialize_user_tokens(user_id: str) -> bool:
    """Initialize user with 100 free tokens"""
    if not FIREBASE_AVAILABLE:
        return True
    
    try:
        # Check if user already has tokens
        user_tokens_ref = firebase_service.db.collection('user_tokens').document(user_id)
        existing_tokens = user_tokens_ref.get()
        
        if not existing_tokens.exists:
            # Create new token balance
            token_data = {
                'user_id': user_id,
                'tokens': 100,
                'total_used': 0,
                'created_at': firebase_service.get_timestamp(),
                'updated_at': firebase_service.get_timestamp()
            }
            user_tokens_ref.set(token_data)
            print(f"Initialized 100 tokens for user {user_id}")
        return True
    except Exception as e:
        print(f"Error initializing tokens for user {user_id}: {e}")
        return False

def get_user_tokens(user_id: str) -> dict:
    """Get user's current token balance"""
    if not FIREBASE_AVAILABLE:
        return {
            'user_id': user_id,
            'tokens': 100,
            'total_used': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    try:
        user_tokens_ref = firebase_service.db.collection('user_tokens').document(user_id)
        tokens_doc = user_tokens_ref.get()
        
        if tokens_doc.exists:
            return tokens_doc.to_dict()
        else:
            # Initialize tokens if they don't exist
            initialize_user_tokens(user_id)
            return {
                'user_id': user_id,
                'tokens': 100,
                'total_used': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error getting tokens for user {user_id}: {e}")
        return {
            'user_id': user_id,
            'tokens': 100,
            'total_used': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

def use_tokens(user_id: str, tokens_used: int, operation: str) -> bool:
    """Deduct tokens from user's balance"""
    if not FIREBASE_AVAILABLE:
        return True
    
    try:
        user_tokens_ref = firebase_service.db.collection('user_tokens').document(user_id)
        tokens_doc = user_tokens_ref.get()
        
        if not tokens_doc.exists:
            # Initialize tokens if they don't exist
            initialize_user_tokens(user_id)
            tokens_doc = user_tokens_ref.get()
        
        current_tokens = tokens_doc.to_dict()
        if current_tokens['tokens'] < tokens_used:
            return False  # Insufficient tokens
        
        # Update token balance
        new_balance = current_tokens['tokens'] - tokens_used
        new_total_used = current_tokens['total_used'] + tokens_used
        
        user_tokens_ref.update({
            'tokens': new_balance,
            'total_used': new_total_used,
            'updated_at': firebase_service.get_timestamp()
        })
        
        # Log token usage
        usage_data = {
            'user_id': user_id,
            'tokens_used': tokens_used,
            'operation': operation,
            'created_at': firebase_service.get_timestamp()
        }
        firebase_service.db.collection('token_usage').add(usage_data)
        
        print(f"Used {tokens_used} tokens for {operation} by user {user_id}. Remaining: {new_balance}")
        return True
    except Exception as e:
        print(f"Error using tokens for user {user_id}: {e}")
        return False

def calculate_tokens_needed(resume_count: int) -> int:
    """Calculate tokens needed for resume processing"""
    # 1 token per resume for screening
    return resume_count

# Resume processing functions
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return ""

def extract_email_from_text(text: str) -> str:
    """Extract email address from text with strict validation"""
    # More comprehensive email pattern
    email_pattern = r'\b[A-Za-z0-9]([A-Za-z0-9._%-]*[A-Za-z0-9])?@[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    if emails:
        # Return the first valid email
        return emails[0] if isinstance(emails[0], str) else emails[0][0]
    
    # Fallback: try to find email-like patterns in common locations
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if '@' in line and '.' in line:
            # Look for email in lines that contain @ and .
            words = line.split()
            for word in words:
                if '@' in word and '.' in word:
                    # Basic email validation
                    if word.count('@') == 1 and len(word.split('@')[1].split('.')) >= 2:
                        return word.strip('.,;:()[]{}"\'')
    
    return ""

def extract_phone_from_text(text: str) -> str:
    """Extract phone number from text with strict validation"""
    # More comprehensive phone number patterns
    phone_patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
        r'\+?[0-9]{1,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',  # International
        r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # Simple US format
        r'\+?[0-9]{10,15}',  # Simple international format
    ]
    
    found_phones = []
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        for phone in phones:
            # Clean the phone number
            clean_phone = re.sub(r'[^\d+]', '', phone)
            # Validate phone number length (7-15 digits)
            if 7 <= len(clean_phone.replace('+', '')) <= 15:
                found_phones.append(phone)
    
    if found_phones:
        # Return the first valid phone number
        return found_phones[0]
    
    # Fallback: look for phone-like patterns in contact sections
    lines = text.split('\n')
    for line in lines:
        line = line.strip().lower()
        if 'phone:' in line or 'mobile:' in line or 'tel:' in line or 'contact:' in line:
            # Extract phone after the colon
            parts = line.split(':', 1)
            if len(parts) > 1:
                phone_part = parts[1].strip()
                # Look for digits in the phone part
                digits = re.findall(r'\d+', phone_part)
                if digits:
                    phone = ''.join(digits)
                    if 7 <= len(phone) <= 15:
                        return phone
    
    return ""

def extract_name_from_text(text: str) -> str:
    """Extract name from resume text using strict pattern matching and GPT fallback"""
    try:
        # First, try to extract name using pattern matching
        name = extract_name_with_patterns(text)
        if name and name != "Unknown":
            return name
        
        # If pattern matching fails, use GPT as fallback
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": """Extract the candidate's full name from the resume text. 
                Look for the person's name at the beginning of the document, in header sections, or contact information.
                Return only the full name (first and last name), nothing else.
                If no clear name is found, return "Unknown"."""},
                {"role": "user", "content": f"Resume text: {text[:2000]}"}
            ],
            max_tokens=50,
            temperature=0.1
        )
        name = response.choices[0].message.content.strip()
        return name if name and name != "Unknown" else "Unknown"
    except Exception as e:
        print(f"Error extracting name: {e}")
        return "Unknown"

def extract_name_with_patterns(text: str) -> str:
    """Extract name using pattern matching before GPT fallback"""
    lines = text.split('\n')
    
    # Look for name in the first few lines (common resume format)
    for i, line in enumerate(lines[:10]):  # Check first 10 lines
        line = line.strip()
        if not line:
            continue
            
        # Skip common resume headers
        skip_words = ['resume', 'cv', 'curriculum', 'vitae', 'contact', 'personal', 'information', 'profile', 'objective']
        if any(word in line.lower() for word in skip_words):
            continue
            
        # Look for lines that might contain a name (2-4 words, starts with capital)
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check if it looks like a name (starts with capital letters, no numbers)
            if all(word[0].isupper() and word.isalpha() for word in words):
                # Additional validation: not common resume keywords
                if not any(word.lower() in ['phone', 'email', 'address', 'linkedin', 'github', 'portfolio'] for word in words):
                    return ' '.join(words)
    
    # Look for name patterns in contact information
    for line in lines:
        line = line.strip().lower()
        if 'name:' in line or 'full name:' in line or 'candidate name:' in line:
            # Extract name after the colon
            parts = line.split(':', 1)
            if len(parts) > 1:
                name_part = parts[1].strip()
                words = name_part.split()
                if 2 <= len(words) <= 4:
                    return ' '.join(word.capitalize() for word in words)
    
    return "Unknown"

def analyze_resume_with_gpt(resume_text: str, job_description: str) -> dict:
    """Analyze resume using GPT-4o mini and return score and feedback"""
    try:
        print(f"GPT Analysis: Starting analysis with {len(resume_text)} characters of text")
        
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": """You are an expert HR recruiter. Analyze the resume against the job description and provide:
1. A score from 0-10 (10 being perfect match)
2. A brief explanation of why the candidate was/wasn't shortlisted
3. Key strengths and weaknesses

Return your response in this exact JSON format:
{
    "score": 7.5,
    "explanation": "Brief explanation of the decision",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"]
}"""},
                {"role": "user", "content": f"""Job Description:
{job_description}

Resume:
{resume_text[:3000]}

Analyze this resume against the job description and provide your assessment."""}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        print(f"GPT Analysis: Received response from OpenAI")
        result = response.choices[0].message.content.strip()
        print(f"GPT Analysis: Response length: {len(result)} characters")
        
        # Try to parse JSON response
        try:
            import json
            analysis = json.loads(result)
            print(f"GPT Analysis: Successfully parsed JSON response")
            return {
                "score": float(analysis.get("score", 0)),
                "explanation": analysis.get("explanation", "No explanation provided"),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", [])
            }
        except json.JSONDecodeError as json_error:
            print(f"GPT Analysis: JSON parsing failed: {json_error}")
            print(f"GPT Analysis: Raw response: {result}")
            # Fallback if JSON parsing fails
            return {
                "score": 5.0,
                "explanation": "Unable to parse detailed analysis",
                "strengths": [],
                "weaknesses": []
            }
            
    except Exception as e:
        print(f"GPT Analysis: Error in GPT analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "score": 0.0,
            "explanation": "Error occurred during analysis",
            "strengths": [],
            "weaknesses": []
        }

def categorize_resume(score: float) -> str:
    """Categorize resume based on score"""
    if score >= 7.0:
        return "selected"
    elif score >= 4.0:
        return "considered"
    else:
        return "rejected"

def validate_extracted_data(name: str, email: str, phone: str) -> dict:
    """Validate and clean extracted data"""
    validated = {
        'name': name,
        'email': email,
        'phone': phone
    }
    
    # Validate name
    if name and name != "Unknown":
        # Check if name contains only letters and spaces
        if re.match(r'^[a-zA-Z\s]+$', name):
            validated['name'] = name.strip().title()
        else:
            validated['name'] = "Unknown"
    
    # Validate email
    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            validated['email'] = email.strip().lower()
        else:
            validated['email'] = ""
    
    # Validate phone
    if phone:
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^\d+]', '', phone)
        if 7 <= len(clean_phone.replace('+', '')) <= 15:
            validated['phone'] = clean_phone
        else:
            validated['phone'] = ""
    
    return validated

def extract_company_info_from_jd(job_description: str) -> dict:
    """Extract company and position information from job description using GPT"""
    try:
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": """Extract the following information from the job description:
1. Company name
2. Position title
3. Department or team
4. Location (if mentioned)
5. Key requirements or skills mentioned

Return in this exact JSON format:
{
    "company_name": "Company Name",
    "position_title": "Job Title",
    "department": "Department/Team",
    "location": "City, State/Country",
    "key_skills": ["skill1", "skill2", "skill3"]
}"""},
                {"role": "user", "content": f"Job Description:\n{job_description}"}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        import json
        return json.loads(result)
    except Exception as e:
        print(f"Error extracting company info: {e}")
        return {
            "company_name": "Our Company",
            "position_title": "the Position",
            "department": "Our Team",
            "location": "",
            "key_skills": []
        }

def generate_personalized_email_with_gpt(candidate_data: dict, company_info: dict, category: str) -> str:
    """Generate personalized email content using GPT with candidate and company data"""
    try:
        # Prepare context for GPT
        candidate_name = candidate_data.get("name", "Candidate")
        candidate_email = candidate_data.get("email", "")
        candidate_phone = candidate_data.get("phone", "")
        candidate_strengths = candidate_data.get("strengths", [])
        candidate_weaknesses = candidate_data.get("weaknesses", [])
        candidate_score = candidate_data.get("score", 0)
        
        company_name = company_info.get("company_name", "Our Company")
        position_title = company_info.get("position_title", "the Position")
        department = company_info.get("department", "Our Team")
        location = company_info.get("location", "")
        
        # Create personalized prompts based on category
        if category == "selected":
            prompt = f"""Write a personalized email to {candidate_name} informing them they've been selected for the next round of interviews for the {position_title} position at {company_name}.

Use this information:
- Candidate: {candidate_name}
- Position: {position_title}
- Company: {company_name}
- Department: {department}
- Location: {location}
- Candidate's strengths: {', '.join(candidate_strengths) if candidate_strengths else 'their qualifications'}
- Score: {candidate_score}/10

Make it personal and encouraging. Include next steps."""
            
        elif category == "rejected":
            prompt = f"""Write a respectful and encouraging rejection email to {candidate_name} for the {position_title} position at {company_name}.

Use this information:
- Candidate: {candidate_name}
- Position: {position_title}
- Company: {company_name}
- Department: {department}
- Location: {location}
- Candidate's strengths: {', '.join(candidate_strengths) if candidate_strengths else 'their qualifications'}

Be polite, respectful, and encouraging for future opportunities."""
            
        else:  # considered
            prompt = f"""Write a professional email to {candidate_name} informing them they are being considered for the {position_title} position at {company_name}.

Use this information:
- Candidate: {candidate_name}
- Position: {position_title}
- Company: {company_name}
- Department: {department}
- Location: {location}
- Candidate's strengths: {', '.join(candidate_strengths) if candidate_strengths else 'their qualifications'}

Be encouraging and professional."""
        
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional HR assistant. Write personalized, professional emails that are warm and human. Use the candidate's name and specific details from their application."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating personalized email: {e}")
        # Fallback to basic template
        return generate_fallback_email(candidate_data, company_info, category)

def generate_fallback_email(candidate_data: dict, company_info: dict, category: str) -> str:
    """Generate fallback email template when GPT fails"""
    candidate_name = candidate_data.get("name", "Candidate")
    company_name = company_info.get("company_name", "Our Company")
    position_title = company_info.get("position_title", "the Position")
    
    if category == "selected":
        return f"""Subject: Congratulations - You've Been Selected for the Next Round

Dear {candidate_name},

I hope this message finds you well.

Thank you for your interest in the {position_title} at {company_name}. We are pleased to inform you that your application has been reviewed, and we are considering you for the next steps in our recruitment process.

Your qualifications and experience have impressed our team, and we believe you would be a valuable addition to our organization.

You may be contacted soon for further discussions or to schedule an interview. We appreciate your patience as we continue our evaluation process.

Thank you once again for your interest in joining our team. We look forward to the possibility of working together.

Best regards,
HR Team
{company_name}"""

    elif category == "rejected":
        return f"""Subject: Application Status Update

Dear {candidate_name},

I hope this message finds you well.

Thank you for your interest in the {position_title} at {company_name}. After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.

We appreciate your interest in our company and encourage you to apply for future opportunities that may be a better fit.

Thank you once again for your interest in joining our team.

Best regards,
HR Team
{company_name}"""

    else:  # considered
        return f"""Subject: Application Status - Under Consideration

Dear {candidate_name},

I hope this message finds you well.

Thank you for your interest in the {position_title} at {company_name}. We are currently reviewing all applications and your profile is under consideration.

You may be contacted soon for further discussions or to schedule an interview. We appreciate your patience as we continue our evaluation process.

Thank you once again for your interest in joining our team. We look forward to the possibility of working together.

Best regards,
HR Team
{company_name}"""

def generate_email_content_with_gpt(category: str) -> str:
    """Legacy function - kept for backward compatibility"""
    return generate_personalized_email_with_gpt({}, {}, category)

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Resume Shortlisting API is running"}

@app.get("/test-firebase")
async def test_firebase():
    """Test Firebase connection"""
    if not FIREBASE_AVAILABLE:
        return {"message": "Firebase not configured", "available": False}
    
    try:
        # Try to create a test document
        test_data = {
            "test": True,
            "timestamp": firebase_service.get_timestamp()
        }
        doc_ref = firebase_service.db.collection('test').add(test_data)
        return {
            "message": "Firebase connection successful", 
            "available": True,
            "test_doc_id": doc_ref[1].id
        }
    except Exception as e:
        return {
            "message": f"Firebase connection failed: {str(e)}", 
            "available": False,
            "error": str(e)
        }

@app.post("/test-data/{user_id}")
async def create_test_data(user_id: str):
    """Create test data for a user"""
    if not FIREBASE_AVAILABLE:
        return {"message": "Firebase not configured", "created": False}
    
    try:
        # Create test resume data
        test_resumes = [
            {
                "candidateName": "John Doe",
                "candidateEmail": "john.doe@example.com",
                "candidatePhone": "+1234567890",
                "fileName": "john_doe_resume.pdf",
                "category": "selected",
                "score": 8.5,
                "explanation": "Strong technical background with relevant experience",
                "strengths": ["Python", "Machine Learning", "Data Analysis"],
                "weaknesses": ["Limited leadership experience"],
                "uploadedAt": firebase_service.get_timestamp()
            },
            {
                "candidateName": "Jane Smith",
                "candidateEmail": "jane.smith@example.com",
                "candidatePhone": "+1234567891",
                "fileName": "jane_smith_resume.pdf",
                "category": "considered",
                "score": 6.5,
                "explanation": "Good technical skills but needs more experience",
                "strengths": ["JavaScript", "React", "Node.js"],
                "weaknesses": ["Limited backend experience"],
                "uploadedAt": firebase_service.get_timestamp()
            },
            {
                "candidateName": "Bob Johnson",
                "candidateEmail": "bob.johnson@example.com",
                "candidatePhone": "+1234567892",
                "fileName": "bob_johnson_resume.pdf",
                "category": "rejected",
                "score": 3.5,
                "explanation": "Does not meet minimum requirements",
                "strengths": ["Basic HTML", "CSS"],
                "weaknesses": ["No relevant experience", "Limited technical skills"],
                "uploadedAt": firebase_service.get_timestamp()
            }
        ]
        
        # Create test uploaded files
        test_files = [
            {
                "fileName": "john_doe_resume.pdf",
                "fileSize": 245760,
                "fileType": "pdf",
                "s3Url": "https://example.com/john_doe_resume.pdf",
                "status": "processed",
                "uploadedAt": firebase_service.get_timestamp()
            },
            {
                "fileName": "jane_smith_resume.pdf",
                "fileSize": 189440,
                "fileType": "pdf",
                "s3Url": "https://example.com/jane_smith_resume.pdf",
                "status": "processed",
                "uploadedAt": firebase_service.get_timestamp()
            },
            {
                "fileName": "bob_johnson_resume.pdf",
                "fileSize": 156672,
                "fileType": "pdf",
                "s3Url": "https://example.com/bob_johnson_resume.pdf",
                "status": "processed",
                "uploadedAt": firebase_service.get_timestamp()
            }
        ]
        
        # Store test resume data
        for resume in test_resumes:
            firebase_service.store_resume_data(user_id, resume)
        
        # Store test uploaded files
        for file_data in test_files:
            firebase_service.store_uploaded_file(user_id, file_data)
        
        return {
            "message": f"Test data created successfully for user {user_id}",
            "created": True,
            "resumes_created": len(test_resumes),
            "files_created": len(test_files)
        }
        
    except Exception as e:
        return {
            "message": f"Error creating test data: {str(e)}",
            "created": False,
            "error": str(e)
        }

@app.post("/test-upload")
async def test_upload(resumes: List[UploadFile] = File(...)):
    """Test endpoint to check if files are being received correctly"""
    try:
        print(f"Test endpoint received {len(resumes)} files")
        for i, resume in enumerate(resumes):
            print(f"  File {i+1}: {resume.filename}, size: {resume.size if hasattr(resume, 'size') else 'unknown'}")
        
        return {
            "message": f"Successfully received {len(resumes)} files",
            "files": [{"name": resume.filename, "size": resume.size if hasattr(resume, 'size') else 'unknown'} for resume in resumes]
        }
    except Exception as e:
        print(f"Test endpoint error: {e}")
        return {"error": str(e)}

async def process_single_resume(
    resume_file: UploadFile,
    job_description: str,
    user_id: str = None,
    resume_index: int = 0
) -> Dict[str, Any]:
    """Process a single resume asynchronously"""
    temp_file_path = None
    try:
        print(f"Starting to process: {resume_file.filename}")
        
        # Read file content
        content = await resume_file.read()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{resume_file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Extract text based on file type
        file_extension = resume_file.filename.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            text = extract_text_from_pdf(temp_file_path)
        elif file_extension in ['doc', 'docx']:
            text = extract_text_from_docx(temp_file_path)
        else:
            text = content.decode('utf-8', errors='ignore')
        
        # Extract basic information
        email = extract_email_from_text(text)
        name = extract_name_from_text(text)
        phone = extract_phone_from_text(text)
        
        # Validate and clean the extracted data
        validated_data = validate_extracted_data(name, email, phone)
        
        # Upload to S3 if available
        s3_url = None
        if S3_AVAILABLE and user_id:
            try:
                s3_url = s3_service.upload_resume_from_bytes(
                    content, 
                    user_id, 
                    resume_file.filename
                )
            except Exception as s3_error:
                print(f"S3 upload failed: {s3_error}")
        
        # Store uploaded file information if user is authenticated
        if user_id and FIREBASE_AVAILABLE:
            try:
                file_data = {
                    "fileName": resume_file.filename,
                    "fileSize": len(content),
                    "fileType": file_extension,
                    "s3Url": s3_url,
                    "status": "processed"
                }
                firebase_service.store_uploaded_file(user_id, file_data)
            except Exception as file_error:
                print(f"Error storing uploaded file info: {file_error}")
        
        # Analyze resume with GPT-4o mini (async)
        if ASYNC_GPT_AVAILABLE:
            analysis = await gpt_service.analyze_resume_async(text, job_description)
        else:
            # Fallback to synchronous GPT
            analysis = analyze_resume_with_gpt(text, job_description)
        
        score = analysis["score"]
        category = categorize_resume(score)
        
        # Create resume data structure
        resume_data = {
            "id": f"resume_{resume_index}",
            "name": validated_data['name'],
            "email": validated_data['email'],
            "phone": validated_data['phone'],
            "s3_url": s3_url,
            "fileName": resume_file.filename,
            "score": score,
            "category": category,
            "content": text,
            "explanation": analysis.get("explanation", "No explanation provided"),
            "strengths": analysis.get("strengths", []),
            "weaknesses": analysis.get("weaknesses", [])
        }
        
        # Store in Firebase if user_id provided
        if user_id and FIREBASE_AVAILABLE:
            try:
                firebase_service.store_resume_data(user_id, {
                    "candidateName": validated_data['name'],
                    "candidateEmail": validated_data['email'],
                    "candidatePhone": validated_data['phone'],
                    "s3Url": s3_url,
                    "fileName": resume_file.filename,
                    "category": category,
                    "score": score,
                    "content": text,
                    "explanation": analysis.get("explanation", ""),
                    "strengths": analysis.get("strengths", []),
                    "weaknesses": analysis.get("weaknesses", []),
                    "uploadedAt": datetime.now()
                })
            except Exception as e:
                print(f"Firebase storage failed: {e}")
        
        return {"success": True, "data": resume_data, "category": category}
        
    except Exception as e:
        print(f"Error processing {resume_file.filename}: {e}")
        import traceback
        traceback.print_exc()
        
        # Return fallback resume entry
        return {
            "success": False,
            "data": {
                "id": f"resume_{resume_index}",
                "name": "Unknown",
                "email": "",
                "phone": "",
                "s3_url": None,
                "fileName": resume_file.filename,
                "score": 0.0,
                "category": "rejected",
                "explanation": f"Error processing resume: {str(e)}",
                "strengths": [],
                "weaknesses": []
            },
            "category": "rejected"
        }
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                print(f"Error cleaning up temp file {cleanup_error}")

@app.post("/process")
async def process_resumes(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(None),
    job_description_file: UploadFile = File(None),
    user_id: str = Form(None)
):
    """Process uploaded resumes asynchronously in parallel batches"""
    try:
        print(f"Received {len(resumes)} resume files for processing")
        
        # Check token balance if user is authenticated
        if user_id:
            tokens_needed = calculate_tokens_needed(len(resumes))
            user_tokens = get_user_tokens(user_id)
            
            if user_tokens['tokens'] < tokens_needed:
                raise HTTPException(
                    status_code=402, 
                    detail=f"Insufficient tokens. You need {tokens_needed} tokens but only have {user_tokens['tokens']}. Please purchase more tokens."
                )
        
        # Process job description - either from text or file
        final_job_description = job_description
        if job_description_file:
            print(f"Processing JD file: {job_description_file.filename}")
            try:
                # Read JD file content
                jd_content = await job_description_file.read()
                
                # Save JD file temporarily and extract text
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{job_description_file.filename.split('.')[-1]}") as temp_jd_file:
                    temp_jd_file.write(jd_content)
                    temp_jd_file_path = temp_jd_file.name
                
                try:
                    # Extract text from JD file based on file type
                    if job_description_file.filename.lower().endswith('.pdf'):
                        jd_text = extract_text_from_pdf(temp_jd_file_path)
                    elif job_description_file.filename.lower().endswith(('.doc', '.docx')):
                        jd_text = extract_text_from_docx(temp_jd_file_path)
                    elif job_description_file.filename.lower().endswith('.txt'):
                        jd_text = jd_content.decode('utf-8', errors='ignore')
                    else:
                        # Default to text extraction
                        jd_text = jd_content.decode('utf-8', errors='ignore')
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_jd_file_path):
                        os.unlink(temp_jd_file_path)
                
                final_job_description = jd_text
                print(f"Extracted {len(jd_text)} characters from JD file")
            except Exception as e:
                print(f"Error processing JD file: {e}")
                # Fall back to text JD if file processing fails
                if not job_description:
                    raise HTTPException(status_code=400, detail="Failed to process job description file and no text job description provided")
        
        if not final_job_description:
            raise HTTPException(status_code=400, detail="No job description provided")
        
        print(f"Using async parallel processing for {len(resumes)} resumes")
        
        # Process resumes in parallel batches
        # Use semaphore to limit concurrent GPT API calls (5 at a time)
        semaphore = asyncio.Semaphore(5)
        
        async def process_with_limit(resume_file: UploadFile, index: int):
            async with semaphore:
                return await process_single_resume(
                    resume_file,
                    final_job_description,
                    user_id,
                    index
                )
        
        # Create tasks for all resumes
        tasks = [process_with_limit(resume, i) for i, resume in enumerate(resumes)]
        
        # Process all resumes in parallel
        print(f"Processing {len(tasks)} resumes in parallel...")
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by category
        results = {
            "selected": [],
            "rejected": [],
            "considered": []
        }
        
        for result in results_list:
            if isinstance(result, Exception):
                print(f"Error in parallel processing: {result}")
                continue
            
            if result.get("success"):
                category = result.get("category", "rejected")
                results[category].append(result["data"])
            else:
                results["rejected"].append(result["data"])
        
        # Deduct tokens after all resumes are processed
        tokens_used = 0
        if user_id:
            tokens_used = calculate_tokens_needed(len(resumes))
            success = use_tokens(user_id, tokens_used, "resume_screening")
            if not success:
                print(f"Warning: Failed to deduct tokens for user {user_id}")

        # Print processing summary
        total_processed = len(results['selected']) + len(results['rejected']) + len(results['considered'])
        print(f"Processing complete: {total_processed} resumes processed out of {len(resumes)} uploaded")
        print(f"Results: {len(results['selected'])} selected, {len(results['considered'])} considered, {len(results['rejected'])} rejected")

        # Include metadata in the response
        metadata = {
            "total_uploaded": len(resumes),
            "job_description": job_description,
            "processed_at": datetime.now().isoformat(),
            "user_id": user_id,
            "tokens_used": tokens_used if user_id else 0
        }

        return {
            "data": results,
            "metadata": metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-email")
async def generate_email(category: str, job_description: str = None, candidate_data: dict = None):
    """Generate personalized email content for a specific category"""
    try:
        # Extract company info from job description if provided
        company_info = {}
        if job_description:
            company_info = extract_company_info_from_jd(job_description)
        
        # Use provided candidate data or default
        candidate_info = candidate_data or {}
        
        # Generate personalized email
        email_content = generate_personalized_email_with_gpt(candidate_info, company_info, category)
        return {"emailContent": email_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-personalized-emails")
async def generate_personalized_emails(
    job_description: str,
    resumes: List[dict],
    category: str
):
    """Generate personalized emails for multiple candidates"""
    try:
        # Extract company info from job description
        company_info = extract_company_info_from_jd(job_description)
        
        personalized_emails = []
        
        for resume in resumes:
            try:
                # Generate personalized email for this candidate
                email_content = generate_personalized_email_with_gpt(resume, company_info, category)
                
                personalized_emails.append({
                    "candidate_name": resume.get("name", "Candidate"),
                    "candidate_email": resume.get("email", ""),
                    "email_content": email_content,
                    "category": category
                })
            except Exception as e:
                print(f"Error generating email for {resume.get('name', 'Unknown')}: {e}")
                # Add fallback email
                personalized_emails.append({
                    "candidate_name": resume.get("name", "Candidate"),
                    "candidate_email": resume.get("email", ""),
                    "email_content": generate_fallback_email(resume, company_info, category),
                    "category": category
                })
        
        return {
            "personalized_emails": personalized_emails,
            "company_info": company_info,
            "total_emails": len(personalized_emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-emails")
async def send_emails(email_request: EmailRequest):
    """Send bulk emails to candidates"""
    try:
        # Email configuration (you should set these in environment variables)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            raise HTTPException(status_code=500, detail="Email configuration not set")
        
        sent_count = 0
        
        for resume in email_request.resumes:
            if resume.get("email"):
                try:
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = email_user
                    msg['To'] = resume["email"]
                    msg['Subject'] = "Application Status Update"
                    
                    # Add body
                    msg.attach(MIMEText(email_request.emailContent, 'plain'))
                    
                    # Send email
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(email_user, email_password)
                    text = msg.as_string()
                    server.sendmail(email_user, resume["email"], text)
                    server.quit()
                    
                    sent_count += 1
                    
                except Exception as e:
                    print(f"Error sending email to {resume['email']}: {e}")
                    continue
        
        return EmailResponse(
            message=f"Emails sent successfully to {sent_count} candidates",
            sent_count=sent_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-personalized-emails")
async def send_personalized_emails(
    job_description: str,
    resumes: List[dict],
    category: str
):
    """Send personalized emails to candidates using extracted data from JD and resumes"""
    try:
        # Email configuration
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            print(f"Email configuration missing - USER: {email_user}, PASSWORD: {'SET' if email_password else 'NOT SET'}")
            raise HTTPException(status_code=500, detail="Email configuration not set. Please check your .env file.")
        
        # Extract company info from job description
        company_info = extract_company_info_from_jd(job_description)
        
        sent_count = 0
        failed_emails = []
        
        for resume in resumes:
            if resume.get("email"):
                try:
                    # Generate personalized email for this candidate
                    email_content = generate_personalized_email_with_gpt(resume, company_info, category)
                    
                    # Extract subject from email content
                    lines = email_content.split('\n')
                    subject = "Application Status Update"
                    body = email_content
                    
                    # Look for subject line
                    for line in lines:
                        if line.startswith("Subject:"):
                            subject = line.replace("Subject:", "").strip()
                            # Remove subject line from body
                            body = '\n'.join(lines[lines.index(line)+1:])
                            break
                    
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = email_user
                    msg['To'] = resume["email"]
                    msg['Subject'] = subject
                    
                    # Add body
                    msg.attach(MIMEText(body, 'plain'))
                    
                    # Send email
                    print(f"Attempting to send email to {resume.get('name', 'Unknown')} at {resume['email']}")
                    print(f"Using SMTP server: {smtp_server}:{smtp_port}")
                    print(f"Using email user: {email_user}")
                    
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(email_user, email_password)
                    text = msg.as_string()
                    server.sendmail(email_user, resume["email"], text)
                    server.quit()
                    
                    sent_count += 1
                    print(f"✅ Sent personalized email to {resume.get('name', 'Unknown')} at {resume['email']}")
                    
                except smtplib.SMTPAuthenticationError as e:
                    error_msg = f"SMTP Authentication failed: {e}"
                    print(f"❌ {error_msg}")
                    failed_emails.append({
                        "name": resume.get("name", "Unknown"),
                        "email": resume["email"],
                        "error": error_msg
                    })
                    continue
                except smtplib.SMTPException as e:
                    error_msg = f"SMTP Error: {e}"
                    print(f"❌ {error_msg}")
                    failed_emails.append({
                        "name": resume.get("name", "Unknown"),
                        "email": resume["email"],
                        "error": error_msg
                    })
                    continue
                except Exception as e:
                    error_msg = f"Unexpected error: {e}"
                    print(f"❌ {error_msg}")
                    failed_emails.append({
                        "name": resume.get("name", "Unknown"),
                        "email": resume["email"],
                        "error": error_msg
                    })
                    continue
        
        return {
            "message": f"Personalized emails sent successfully to {sent_count} candidates",
            "sent_count": sent_count,
            "failed_emails": failed_emails,
            "company_info": company_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store-resume-data")
async def store_resume_data(request: ResumeDataRequest):
    """Store simplified resume data in Firebase (only name, email, phone, s3_url)"""
    print(f"Storing resume data for user: {request.user_id}")
    print(f"Number of resumes to store: {len(request.resume_data)}")
    
    if not FIREBASE_AVAILABLE:
        print("Firebase not available - data not stored")
        return ResumeDataResponse(
            message="Firebase not configured - data not stored",
            stored_count=0
        )
    
    try:
        stored_count = 0
        
        for resume in request.resume_data:
            try:
                # Create simplified resume data structure
                simplified_resume = {
                    "candidateName": resume.get("candidateName", resume.get("name", "Unknown")),
                    "candidateEmail": resume.get("candidateEmail", resume.get("email", "")),
                    "candidatePhone": resume.get("candidatePhone", resume.get("phone", "")),
                    "s3Url": resume.get("s3Url", resume.get("s3_url", "")),
                    "fileName": resume.get("fileName", ""),
                    "category": resume.get("category", "rejected"),
                    "score": resume.get("score", 0.0),
                    "content": resume.get("content", ""),  # Store the actual resume content
                    "explanation": resume.get("explanation", ""),
                    "strengths": resume.get("strengths", []),
                    "weaknesses": resume.get("weaknesses", []),
                    "uploadedAt": firebase_service.get_timestamp()
                }
                
                print(f"Storing resume: {simplified_resume['candidateName']} - {simplified_resume['category']}")
                
                # Store in Firebase
                firebase_service.store_resume_data(request.user_id, simplified_resume)
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing resume data: {e}")
                continue
        
        print(f"Successfully stored {stored_count} resume records for user {request.user_id}")
        return ResumeDataResponse(
            message=f"Successfully stored {stored_count} resume records",
            stored_count=stored_count
        )
        
    except Exception as e:
        print(f"Error in store_resume_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-resume-data/{user_id}")
async def get_user_resume_data(user_id: str, limit: int = 100):
    """Get resume data for a specific user"""
    print(f"Getting resume data for user: {user_id}")
    if not FIREBASE_AVAILABLE:
        print("Firebase not available - returning empty data")
        return {"data": []}
    
    try:
        resume_data = firebase_service.get_user_resume_data(user_id, limit)
        print(f"Retrieved {len(resume_data)} resume records for user {user_id}")
        return {"data": resume_data}
    except Exception as e:
        print(f"Error getting resume data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get statistics for a user's resume data"""
    print(f"Getting stats for user: {user_id}")
    if not FIREBASE_AVAILABLE:
        print("Firebase not available - returning zero stats")
        return {"stats": {"total": 0, "selected": 0, "considered": 0, "rejected": 0}}
    
    try:
        stats = firebase_service.get_user_stats(user_id)
        print(f"Retrieved stats for user {user_id}: {stats}")
        return {"stats": stats}
    except Exception as e:
        print(f"Error getting stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-uploaded-files/{user_id}")
async def get_user_uploaded_files(user_id: str, limit: int = 100):
    """Get uploaded files for a specific user"""
    print(f"Getting uploaded files for user: {user_id}")
    if not FIREBASE_AVAILABLE:
        print("Firebase not available - returning empty files")
        return {"files": []}
    
    try:
        files = firebase_service.get_user_uploaded_files(user_id, limit)
        print(f"Retrieved {len(files)} uploaded files for user {user_id}")
        return {"files": files}
    except Exception as e:
        print(f"Error getting uploaded files for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/uploaded-file/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file"""
    if not FIREBASE_AVAILABLE:
        return {"message": "Firebase not configured"}
    
    try:
        success = firebase_service.delete_uploaded_file(file_id)
        if success:
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/update-resume-category/{resume_id}")
async def update_resume_category(resume_id: str, category: str):
    """Update the category of a resume"""
    if not FIREBASE_AVAILABLE:
        return {"message": "Firebase not configured"}
    
    try:
        success = firebase_service.update_resume_category(resume_id, category)
        if success:
            return {"message": "Resume category updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update resume category")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Authentication endpoints
@app.post("/auth/register")
async def register_user(request: AuthRequest):
    """Register a new user"""
    if not FIREBASE_AVAILABLE:
        # Return a mock response for development
        import uuid
        user_id = str(uuid.uuid4())
        user_profile = {
            "uid": user_id,
            "email": request.email,
            "phoneNumber": request.phoneNumber,
            "displayName": request.displayName,
            "createdAt": "2024-01-01T00:00:00Z",
            "lastLoginAt": "2024-01-01T00:00:00Z"
        }
        
        return AuthResponse(
            success=True,
            message="User created successfully (Firebase not configured - using mock data)",
            user_id=user_id,
            user_profile=user_profile
        )
    
    try:
        # Create user in Firebase Auth
        user_id = firebase_service.create_user(request.email, request.password, request.displayName)
        
        # Create user profile in Firestore
        user_profile = {
            "uid": user_id,
            "email": request.email,
            "phoneNumber": request.phoneNumber,
            "displayName": request.displayName,
            "createdAt": firebase_service.get_timestamp(),
            "lastLoginAt": firebase_service.get_timestamp()
        }
        
        firebase_service.store_user_profile(user_id, user_profile)
        
        return AuthResponse(
            success=True,
            message="User created successfully",
            user_id=user_id,
            user_profile=user_profile
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login_user(request: LoginRequest):
    """Login a user"""
    if not FIREBASE_AVAILABLE:
        # Return a mock response for development
        import uuid
        user_id = str(uuid.uuid4())
        user_profile = {
            "uid": user_id,
            "email": request.email,
            "phoneNumber": None,
            "displayName": "Test User",
            "createdAt": "2024-01-01T00:00:00Z",
            "lastLoginAt": "2024-01-01T00:00:00Z"
        }
        
        return AuthResponse(
            success=True,
            message="Login successful (Firebase not configured - using mock data)",
            user_id=user_id,
            user_profile=user_profile
        )
    
    try:
        # Verify user credentials
        user_id = firebase_service.verify_user(request.email, request.password)
        
        # Get user profile
        user_profile = firebase_service.get_user_profile(user_id)
        
        # If user profile doesn't exist, create a basic one
        if not user_profile:
            user_profile = {
                "uid": user_id,
                "email": request.email,
                "phoneNumber": None,
                "displayName": None,
                "createdAt": firebase_service.get_timestamp(),
                "lastLoginAt": firebase_service.get_timestamp()
            }
            firebase_service.store_user_profile(user_id, user_profile)
        else:
            # Update last login
            user_profile["lastLoginAt"] = firebase_service.get_timestamp()
            firebase_service.store_user_profile(user_id, user_profile)
        
        return AuthResponse(
            success=True,
            message="Login successful",
            user_id=user_id,
            user_profile=user_profile
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/auth/user/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile"""
    if not FIREBASE_AVAILABLE:
        # Return mock profile for development
        user_profile = {
            "uid": user_id,
            "email": "test@example.com",
            "phoneNumber": None,
            "displayName": "Test User",
            "createdAt": "2024-01-01T00:00:00Z",
            "lastLoginAt": "2024-01-01T00:00:00Z"
        }
        return {"user_profile": user_profile}
    
    try:
        user_profile = firebase_service.get_user_profile(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"user_profile": user_profile}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/auth/user/{user_id}")
async def update_user_profile(user_id: str, profile_data: dict):
    """Update user profile"""
    if not FIREBASE_AVAILABLE:
        return {"message": "Profile updated successfully (Firebase not configured - using mock data)"}
    
    try:
        success = firebase_service.store_user_profile(user_id, profile_data)
        if success:
            return {"message": "Profile updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Token Management Endpoints
@app.get("/tokens/{user_id}")
async def get_user_token_balance(user_id: str):
    """Get user's token balance"""
    try:
        tokens = get_user_tokens(user_id)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tokens/initialize/{user_id}")
async def initialize_user_tokens_endpoint(user_id: str):
    """Initialize user with 100 free tokens"""
    try:
        success = initialize_user_tokens(user_id)
        if success:
            return {"message": "Tokens initialized successfully", "tokens": 100}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize tokens")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tokens/purchase")
async def purchase_tokens(request: PurchaseTokens):
    """Purchase additional tokens (mock implementation)"""
    try:
        print(f"Purchase request received: user_id={request.user_id}, package={request.token_package}")
        
        # Mock token packages
        token_packages = {
            "standard": {"tokens": 100, "price": 0}
        }
        
        if request.token_package not in token_packages:
            print(f"Invalid token package: {request.token_package}")
            raise HTTPException(status_code=400, detail="Invalid token package")
        
        package = token_packages[request.token_package]
        print(f"Package details: {package}")
        
        # Check if Firebase is available
        if not FIREBASE_AVAILABLE:
            print("Firebase not available")
            raise HTTPException(status_code=500, detail="Firebase service not available")
        
        print("Firebase is available, proceeding with token purchase")
        
        # Add tokens to the user's balance
        user_tokens_ref = firebase_service.db.collection('user_tokens').document(request.user_id)
        tokens_doc = user_tokens_ref.get()
        
        if tokens_doc.exists:
            current_tokens = tokens_doc.to_dict()
            new_balance = current_tokens['tokens'] + package['tokens']
            print(f"Updating existing user tokens: {current_tokens['tokens']} -> {new_balance}")
            
            user_tokens_ref.update({
                'tokens': new_balance,
                'updated_at': firebase_service.get_timestamp()
            })
        else:
            # Initialize with purchased tokens
            token_data = {
                'user_id': request.user_id,
                'tokens': 100 + package['tokens'],  # 100 free + purchased
                'total_used': 0,
                'created_at': firebase_service.get_timestamp(),
                'updated_at': firebase_service.get_timestamp()
            }
            print(f"Creating new user token record: {token_data}")
            user_tokens_ref.set(token_data)
        
        print("Token purchase successful")
        return {
            "message": f"Successfully purchased {package['tokens']} tokens",
            "tokens_added": package['tokens'],
            "price": package['price']
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in purchase_tokens: {e}")
        raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")

# Add a simple health check endpoint
@app.get("/")
async def health_check():
    return {"message": "Resume Shortlisting API is running", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

