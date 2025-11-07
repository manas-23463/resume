# Resume Shortlisting System

A comprehensive resume shortlisting application that automatically categorizes resumes based on job descriptions and provides bulk email functionality.

## Features

- **Bulk Resume Upload**: Upload multiple resumes in PDF, DOC, or DOCX format
- **AI-Powered Categorization**: Automatically categorizes resumes into:
  - ✅ **Selected**: High-scoring resumes (score ≥ 7.0)
  - ⚠️ **Can Be Considered**: Medium-scoring resumes (score 4.0-6.9)
  - ❌ **Rejected**: Low-scoring resumes (score < 4.0)
- **Detailed Analysis**: GPT-4o mini provides explanations for each decision
- **Strengths & Weaknesses**: AI identifies key strengths and areas for improvement
- **Manual Review**: Move resumes between categories after initial processing
- **Bulk Email**: Send personalized emails to candidates in each category
- **GPT-Generated Content**: AI-generated email templates for different categories
- **Modern UI**: Clean, responsive interface with custom color palette

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- React Router for navigation
- Axios for API calls
- Custom CSS with Helvetica font

### Backend
- Python 3.9
- FastAPI for REST API
- OpenAI GPT-4o mini for resume analysis and email generation
- PyPDF2 and python-docx for document parsing
- AI-powered resume scoring and detailed feedback

## Project Structure

```
Resume/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Page components
│   │   └── services/       # API services
│   ├── Dockerfile          # Production build
│   └── Dockerfile.dev      # Development build
├── backend/                # Python backend
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Backend container
├── docker-compose.yml     # Multi-container setup
└── README.md
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- OpenAI API key
- Email credentials (Gmail recommended)

### Environment Variables

Create a `.env` file in the backend directory:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
```

### Local Development

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   uvicorn main:app --reload
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Usage

1. **Upload Resumes**: Drag and drop or select multiple resume files
2. **Enter Job Description**: Paste the job description in the text area
3. **Process Resumes**: Click "Process Resumes" to categorize them
4. **Review Results**: Manually move resumes between categories if needed
5. **Send Emails**: Use bulk email functionality to notify candidates

## API Endpoints

- `POST /process` - Process uploaded resumes
- `POST /generate-email` - Generate email content for a category
- `POST /send-emails` - Send bulk emails to candidates

## Color Palette

- Background: `#fffff4` (Cream)
- Accent: `#e0d2b7` (Light Brown)
- Title: `#340100` (Dark Red)
- Font: Helvetica

## Deployment

The application is deployment-ready with:
- Docker containers for both frontend and backend
- Nginx configuration for production
- Environment variable configuration
- CORS setup for cross-origin requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

