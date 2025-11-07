import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getUserResumeData, getUserStats, getUserUploadedFiles, deleteUploadedFile } from '../services/api';
import TokenBalance from '../components/TokenBalance';

interface ResumeData {
  id: string;
  candidateName: string;
  candidateEmail: string;
  candidatePhone?: string;
  fileName: string;
  category: 'selected' | 'rejected' | 'considered';
  score: number;
  extractedAt: Date;
  userId: string;
}

interface UploadedFile {
  id: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  s3Url?: string;
  status: string;
  uploadedAt: Date;
  userId: string;
}

const DashboardPage = () => {
  const { currentUser, userProfile, logout } = useAuth();
  const [resumeData, setResumeData] = useState<ResumeData[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    selected: 0,
    considered: 0,
    rejected: 0
  });

  useEffect(() => {
    if (currentUser) {
      fetchResumeData();
    }
  }, [currentUser]);

  const fetchResumeData = async () => {
    try {
      setLoading(true);
      console.log('Fetching resume data for user:', currentUser?.uid);
      
      // Fetch resume data, uploaded files, and stats from API
      const [resumeResponse, filesResponse, statsResponse] = await Promise.all([
        getUserResumeData(currentUser?.uid || '', 100),
        getUserUploadedFiles(currentUser?.uid || '', 100),
        getUserStats(currentUser?.uid || '')
      ]);
      
      console.log('Resume response:', resumeResponse);
      console.log('Files response:', filesResponse);
      console.log('Stats response:', statsResponse);
      
      const data: ResumeData[] = resumeResponse.data.map((item: any) => ({
        id: item.id,
        candidateName: item.candidateName,
        candidateEmail: item.candidateEmail,
        candidatePhone: item.candidatePhone,
        fileName: item.fileName,
        category: item.category,
        score: item.score,
        extractedAt: new Date(item.extractedAt)
      }));
      
      const files: UploadedFile[] = filesResponse.files.map((item: any) => ({
        id: item.id,
        fileName: item.fileName,
        fileSize: item.fileSize,
        fileType: item.fileType,
        s3Url: item.s3Url,
        status: item.status,
        uploadedAt: new Date(item.uploadedAt),
        userId: item.userId
      }));
      
      console.log('Processed resume data:', data);
      console.log('Processed uploaded files:', files);
      console.log('Processed stats:', statsResponse.stats);
      
      setResumeData(data);
      setUploadedFiles(files);
      setStats(statsResponse.stats);
    } catch (error) {
      console.error('Error fetching resume data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await deleteUploadedFile(fileId);
      // Refresh the uploaded files list
      const filesResponse = await getUserUploadedFiles(currentUser?.uid || '', 100);
      const files: UploadedFile[] = filesResponse.files.map((item: any) => ({
        id: item.id,
        fileName: item.fileName,
        fileSize: item.fileSize,
        fileType: item.fileType,
        s3Url: item.s3Url,
        status: item.status,
        uploadedAt: new Date(item.uploadedAt),
        userId: item.userId
      }));
      setUploadedFiles(files);
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };


  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="header-left">
          <div className="dashboard-title">
            <h1>Dashboard</h1>
            <p>Welcome back, {userProfile?.displayName || currentUser?.email}</p>
          </div>
        </div>
        <div className="dashboard-actions">
          {currentUser && (
            <TokenBalance 
              userId={currentUser.uid} 
            />
          )}
          <button className="btn btn-secondary" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </div>

      {/* User Profile Info */}
      <div className="profile-card">
        <h2>Your Profile</h2>
        <div className="profile-info">
          <div className="profile-item">
            <strong>Email:</strong> {userProfile?.email}
          </div>
          {userProfile?.phoneNumber && (
            <div className="profile-item">
              <strong>Phone:</strong> {userProfile.phoneNumber}
            </div>
          )}
          <div className="profile-item">
            <strong>Member since:</strong> {userProfile?.createdAt ? new Date(userProfile.createdAt).toLocaleDateString() : 'N/A'}
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Resumes</h3>
          <div className="stat-number">{stats.total}</div>
        </div>
        <div className="stat-card selected">
          <h3>Selected</h3>
          <div className="stat-number">{stats.selected}</div>
        </div>
        <div className="stat-card considered">
          <h3>Considered</h3>
          <div className="stat-number">{stats.considered}</div>
        </div>
        <div className="stat-card rejected">
          <h3>Rejected</h3>
          <div className="stat-number">{stats.rejected}</div>
        </div>
      </div>

      {/* Uploaded Files Section */}
      <div className="uploaded-files-section">
        <h2>Your Uploaded Resumes</h2>
        {uploadedFiles.length === 0 ? (
          <div className="empty-state">
            <p>No uploaded files found. Start by uploading resumes for processing.</p>
          </div>
        ) : (
          <div className="uploaded-files-list">
            {uploadedFiles.map((file) => (
              <div key={file.id} className="uploaded-file-item">
                <div className="file-info">
                  <div className="file-name">{file.fileName}</div>
                  <div className="file-details">
                    <span className="file-size">{formatFileSize(file.fileSize)}</span>
                    <span className="file-type">{file.fileType.toUpperCase()}</span>
                    <span className={`file-status ${file.status}`}>{file.status}</span>
                  </div>
                  <div className="file-date">
                    Uploaded: {file.uploadedAt.toLocaleDateString()} at {file.uploadedAt.toLocaleTimeString()}
                  </div>
                </div>
                <div className="file-actions">
                  {file.s3Url && (
                    <a 
                      href={file.s3Url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-sm"
                    >
                      Download
                    </a>
                  )}
                  <button 
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDeleteFile(file.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Resume Data */}
      <div className="resume-data-section">
        <h2>Recent Resume Processing</h2>
        {resumeData.length === 0 ? (
          <div className="empty-state">
            <p>No resume data found. Start by uploading and processing resumes.</p>
          </div>
        ) : (
          <div className="resume-data-list">
            {resumeData.slice(0, 10).map((resume) => (
              <div key={resume.id} className="resume-data-item">
                <div className="resume-data-header">
                  <div className="resume-data-name">{resume.candidateName}</div>
                  <div className={`resume-data-category ${resume.category}`}>
                    {resume.category}
                  </div>
                </div>
                <div className="resume-data-details">
                  <div className="resume-data-email">{resume.candidateEmail}</div>
                  {resume.candidatePhone && (
                    <div className="resume-data-phone">{resume.candidatePhone}</div>
                  )}
                  <div className="resume-data-score">Score: {resume.score.toFixed(1)}/10</div>
                  <div className="resume-data-date">
                    Processed: {resume.extractedAt.toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
