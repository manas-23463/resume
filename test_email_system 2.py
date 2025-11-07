#!/usr/bin/env python3
"""
Test script for the personalized email system
"""

import requests
import json

# Test data
job_description = """
Software Engineer Position at TechCorp Inc.

We are seeking a talented Software Engineer to join our development team in San Francisco, CA.

Requirements:
- 3+ years of Python experience
- Experience with React and JavaScript
- Knowledge of AWS and cloud technologies
- Strong problem-solving skills

This is a full-time position in our Engineering department.
"""

test_resumes = [
    {
        "name": "John Smith",
        "email": "john.smith@example.com",
        "phone": "+1234567890",
        "score": 8.5,
        "category": "selected",
        "strengths": ["Python", "React", "AWS"],
        "weaknesses": ["Limited leadership experience"]
    },
    {
        "name": "Jane Doe", 
        "email": "jane.doe@example.com",
        "phone": "+1234567891",
        "score": 6.0,
        "category": "considered",
        "strengths": ["JavaScript", "Node.js"],
        "weaknesses": ["Limited Python experience"]
    }
]

def test_generate_personalized_emails():
    """Test the personalized email generation endpoint"""
    print("Testing personalized email generation...")
    
    try:
        response = requests.post(
            "http://localhost:8000/generate-personalized-emails",
            json={
                "job_description": job_description,
                "resumes": test_resumes,
                "category": "selected"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully generated {data['total_emails']} personalized emails")
            print(f"Company info extracted: {data['company_info']}")
            
            for email in data['personalized_emails']:
                print(f"\n--- Email for {email['candidate_name']} ---")
                print(email['email_content'][:200] + "...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing email generation: {e}")

def test_extract_company_info():
    """Test company info extraction"""
    print("\nTesting company info extraction...")
    
    try:
        response = requests.post(
            "http://localhost:8000/generate-email",
            params={"category": "selected"},
            json={
                "job_description": job_description,
                "candidate_data": test_resumes[0]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully extracted company info and generated email")
            print(f"Email content preview: {data['emailContent'][:200]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing company info extraction: {e}")

if __name__ == "__main__":
    print("🧪 Testing Personalized Email System")
    print("=" * 50)
    
    # Test company info extraction
    test_extract_company_info()
    
    # Test personalized email generation
    test_generate_personalized_emails()
    
    print("\n" + "=" * 50)
    print("✅ Email system testing complete!")
    print("\nTo test the full system:")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Start the frontend: cd frontend && npm run dev")
    print("3. Upload resumes and job description")
    print("4. Use the 'Send Emails' feature to see personalized emails in action!")



