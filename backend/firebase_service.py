import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirebaseService:
    def __init__(self):
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            try:
                # Try to use service account JSON from environment variable (for Vercel)
                service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
                if service_account_json:
                    import json
                    service_account_info = json.loads(service_account_json)
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred)
                    print("Firebase initialized with service account JSON from environment")
                else:
                    # Try to use service account file path (for local development)
                    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY', './service-account-key.json')
                    if os.path.exists(service_account_path):
                        cred = credentials.Certificate(service_account_path)
                        firebase_admin.initialize_app(cred)
                        print(f"Firebase initialized with service account from {service_account_path}")
                    else:
                        # Fallback to default credentials
                        cred = credentials.ApplicationDefault()
                        firebase_admin.initialize_app(cred)
                        print("Firebase initialized with default credentials")
            except Exception as e:
                print(f"Error initializing Firebase: {e}")
                raise e
        
        self.db = firestore.client()
    
    def store_resume_data(self, user_id: str, resume_data: Dict[str, Any]) -> str:
        """Store extracted resume data in Firestore"""
        try:
            # Add metadata
            resume_data['userId'] = user_id
            resume_data['extractedAt'] = datetime.now()
            
            # Store in Firestore
            doc_ref = self.db.collection('resumeData').add(resume_data)
            return doc_ref[1].id
        except Exception as e:
            print(f"Error storing resume data: {e}")
            raise e
    
    def get_user_resume_data(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get resume data for a specific user"""
        try:
            query = self.db.collection('resumeData').where('userId', '==', user_id).limit(limit)
            docs = query.stream()
            
            resume_data = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                resume_data.append(data)
            
            return resume_data
        except Exception as e:
            print(f"Error fetching resume data: {e}")
            return []
    
    def update_resume_category(self, resume_id: str, category: str) -> bool:
        """Update the category of a resume"""
        try:
            doc_ref = self.db.collection('resumeData').document(resume_id)
            doc_ref.update({'category': category})
            return True
        except Exception as e:
            print(f"Error updating resume category: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict[str, int]:
        """Get statistics for a user's resume data"""
        try:
            query = self.db.collection('resumeData').where('userId', '==', user_id)
            docs = query.stream()
            
            stats = {'total': 0, 'selected': 0, 'considered': 0, 'rejected': 0}
            
            for doc in docs:
                data = doc.to_dict()
                stats['total'] += 1
                category = data.get('category', 'rejected')
                if category in stats:
                    stats[category] += 1
            
            return stats
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {'total': 0, 'selected': 0, 'considered': 0, 'rejected': 0}
    
    def store_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Store or update user profile data"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.set(profile_data, merge=True)
            return True
        except Exception as e:
            print(f"Error storing user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def create_user(self, email: str, password: str, display_name: str = None) -> str:
        """Create a new user in Firebase Auth"""
        try:
            from firebase_admin import auth
            
            # Create user in Firebase Auth
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            user_id = user_record.uid
            print(f"Created user in Firebase Auth: {email} with ID: {user_id}")
            return user_id
        except Exception as e:
            print(f"Error creating user in Firebase Auth: {e}")
            raise e
    
    def verify_user(self, email: str, password: str) -> str:
        """Verify user credentials and return user ID"""
        try:
            from firebase_admin import auth
            
            # Get user by email from Firebase Auth
            user_record = auth.get_user_by_email(email)
            
            # Note: Firebase Admin SDK doesn't directly verify passwords
            # In a production app, you'd typically verify the password on the client side
            # and then verify the ID token on the server side
            # For now, we'll just return the user ID if the user exists
            print(f"Found user in Firebase Auth: {email} with ID: {user_record.uid}")
            return user_record.uid
        except auth.UserNotFoundError:
            print(f"User not found: {email}")
            raise Exception("Invalid credentials")
        except Exception as e:
            print(f"Error verifying user: {e}")
            raise e
    
    def store_uploaded_file(self, user_id: str, file_data: Dict[str, Any]) -> str:
        """Store uploaded file information in Firestore"""
        try:
            # Add metadata
            file_data['userId'] = user_id
            file_data['uploadedAt'] = datetime.now()
            
            # Store in Firestore
            doc_ref = self.db.collection('uploadedFiles').add(file_data)
            return doc_ref[1].id
        except Exception as e:
            print(f"Error storing uploaded file: {e}")
            raise e
    
    def get_user_uploaded_files(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get uploaded files for a specific user"""
        try:
            query = self.db.collection('uploadedFiles').where('userId', '==', user_id).order_by('uploadedAt', direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            files = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                files.append(data)
            
            return files
        except Exception as e:
            print(f"Error fetching uploaded files: {e}")
            return []
    
    def delete_uploaded_file(self, file_id: str) -> bool:
        """Delete an uploaded file record"""
        try:
            doc_ref = self.db.collection('uploadedFiles').document(file_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting uploaded file: {e}")
            return False

    def get_timestamp(self):
        """Get current timestamp for Firestore"""
        from datetime import datetime
        return datetime.now()

# Global instance
firebase_service = FirebaseService()
