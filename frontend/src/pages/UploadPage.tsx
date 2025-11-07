import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { processResumes, storeResumeData } from '../services/api';
import ProcessingOverlay from '../components/ProcessingOverlay';
import TokenBalance from '../components/TokenBalance';
import type { ResumeFile, JDFile, ProcessedResumeFile } from '../types';

const UploadPage = () => {
  const [resumeFiles, setResumeFiles] = useState<ResumeFile[]>([]);
  const [jdFile, setJdFile] = useState<JDFile | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [tokenBalance, setTokenBalance] = useState<number | null>(null);
  const navigate = useNavigate();
  const { currentUser, userProfile } = useAuth();

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const newResumeFiles = files.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9)
    }));
    setResumeFiles(prev => [...prev, ...newResumeFiles]);
    setError('');
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    const newResumeFiles = files.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9)
    }));
    setResumeFiles(prev => [...prev, ...newResumeFiles]);
    setError('');
  };

  const removeFile = (id: string) => {
    setResumeFiles(prev => prev.filter(file => file.id !== id));
  };

  const handleJDFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setJdFile({
        file,
        id: Math.random().toString(36).substr(2, 9)
      });
      setError('');
    }
  };

  const removeJDFile = () => {
    setJdFile(null);
  };

  const handleSubmit = async () => {
    if (resumeFiles.length === 0) {
      setError('Please upload at least one resume file.');
      return;
    }

    if (!jobDescription.trim() && !jdFile) {
      setError('Please enter a job description or upload a job description file.');
      return;
    }

    // Check token balance if user is authenticated
    if (currentUser && tokenBalance !== null) {
      const tokensNeeded = resumeFiles.length;
      if (tokenBalance < tokensNeeded) {
        setError(`Insufficient resume screening tokens. You need ${tokensNeeded} resume screening tokens but only have ${tokenBalance}. Please purchase more resume screening tokens.`);
        return;
      }
    }

    setIsProcessing(true);
    setError('');
    

    try {
      const formData = new FormData();
      console.log(`Preparing to upload ${resumeFiles.length} resume files:`, resumeFiles.map(f => f.file.name));
      
      resumeFiles.forEach(resumeFile => {
        formData.append('resumes', resumeFile.file);
      });
      
      // Add job description - either from text or file
      if (jdFile) {
        formData.append('job_description_file', jdFile.file);
        console.log('Uploading JD file:', jdFile.file.name);
      } else {
        formData.append('job_description', jobDescription);
        console.log('Using text JD:', jobDescription.substring(0, 100) + '...');
      }
      
      // Add user_id if authenticated
      if (currentUser) {
        formData.append('user_id', currentUser.uid);
      }

      const response = await processResumes(formData);
      
      // Store results and metadata in localStorage for the results page
      console.log('Response from backend:', response);
      const resultsWithMetadata = {
        ...response.data,
        metadata: response.metadata || {
          total_uploaded: resumeFiles.length,
          job_description: jobDescription,
          processed_at: new Date().toISOString(),
          user_id: currentUser?.uid
        }
      };
      console.log('Storing in localStorage:', resultsWithMetadata);
      localStorage.setItem('resumeResults', JSON.stringify(resultsWithMetadata));
      
      // Store resume data in Firebase if user is authenticated
      if (currentUser) {
        try {
          const allResumes = [
            ...response.data.selected,
            ...response.data.considered,
            ...response.data.rejected
          ];
          
          // Transform data for Firebase storage
          const resumeDataForFirebase = allResumes.map(resume => ({
            candidateName: resume.name,
            candidateEmail: resume.email,
            candidatePhone: resume.phone || null,
            fileName: resume.fileName || 'Unknown',
            category: resume.category,
            score: resume.score,
            content: resume.content,
            explanation: resume.explanation,
            strengths: resume.strengths,
            weaknesses: resume.weaknesses,
            s3Url: resume.s3_url || ''
          }));
          
          await storeResumeData(currentUser.uid, resumeDataForFirebase);
        } catch (error) {
          console.error('Error storing resume data in Firebase:', error);
          // Don't block the user flow if Firebase storage fails
        }
      }
      
      navigate('/results');
    } catch (err: any) {
      setError(err.response?.data?.message || 'An error occurred while processing resumes.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <div className="header-left">
          <h1 className="title">Resume Shortlisting System</h1>
        </div>
        <div className="header-actions">
          <span className="user-info">Welcome, {userProfile?.displayName || userProfile?.email}</span>
          <button 
            className="btn btn-secondary" 
            onClick={() => navigate('/dashboard')}
          >
            Dashboard
          </button>
        </div>
      </div>
      
      {currentUser && (
        <div className="token-balance-section">
          <TokenBalance 
            userId={currentUser.uid} 
            onTokenUpdate={setTokenBalance}
          />
        </div>
      )}
      
      <div className="card">
        <h2 className="subtitle">Upload Resumes</h2>
        <div 
          className="file-upload"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <p>Drag and drop resume files here, or click to select files</p>
          <input
            type="file"
            multiple
            accept=".pdf,.doc,.docx"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            id="file-upload"
          />
          <label htmlFor="file-upload" className="btn">
            Choose Files
          </label>
        </div>
        
        {resumeFiles.length > 0 && (
          <div className="selected-files-section">
            <h3>Selected Files:</h3>
            <div className="files-grid">
              {resumeFiles.map(resumeFile => (
                <div key={resumeFile.id} className="file-card">
                  <div className="file-icon">
                    📄
                  </div>
                  <div className="file-info">
                    <div className="file-name">{resumeFile.file.name}</div>
                    <div className="file-size">
                      {(resumeFile.file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                  <button
                    className="remove-file-btn"
                    onClick={() => removeFile(resumeFile.id)}
                    title="Remove file"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="subtitle">Job Description</h2>
        
        {/* JD File Upload Section */}
        <div className="jd-upload-section">
          <h3>Upload Job Description File (Optional)</h3>
          <div 
            className="file-upload jd-upload"
            onDragOver={handleDragOver}
            onDrop={(e) => {
              e.preventDefault();
              const file = e.dataTransfer.files[0];
              if (file) {
                setJdFile({
                  file,
                  id: Math.random().toString(36).substr(2, 9)
                });
                setError('');
              }
            }}
          >
            <p>Drag and drop job description file here, or click to select</p>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleJDFileUpload}
              style={{ display: 'none' }}
              id="jd-file-upload"
            />
            <label htmlFor="jd-file-upload" className="btn btn-secondary">
              Choose JD File
            </label>
          </div>
          
          {jdFile && (
            <div className="selected-jd-file">
              <div className="file-card">
                <div className="file-icon">📄</div>
                <div className="file-info">
                  <div className="file-name">{jdFile.file.name}</div>
                  <div className="file-size">
                    {(jdFile.file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
                <button
                  className="remove-file-btn"
                  onClick={removeJDFile}
                  title="Remove JD file"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Text JD Section */}
        <div className="form-group">
          <label className="form-label">
            {jdFile ? 'Or enter job description text (will be ignored if file is uploaded):' : 'Enter the job description:'}
          </label>
          <textarea
            className="form-textarea"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            disabled={!!jdFile}
          />
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={isProcessing || resumeFiles.length === 0 || (!jobDescription.trim() && !jdFile)}
        >
          Process Resumes
        </button>
      </div>

      <ProcessingOverlay 
        key={`processing-${resumeFiles.length}`}
        isVisible={isProcessing} 
        resumeCount={resumeFiles.length}
        resumeFiles={resumeFiles.map(rf => ({
          name: rf.file.name,
          size: rf.file.size,
          type: rf.file.type,
          id: rf.id
        }))}
      />
    </div>
  );
};

export default UploadPage;
