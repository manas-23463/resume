import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BackToTop from '../components/BackToTop';
import ConfettiEffect from '../components/ConfettiEffect';
import ResumeCarousel from '../components/ResumeCarousel';
import { useAuth } from '../contexts/AuthContext';
import type { Resume, ResumeResults } from '../types';

const ResultsPage = () => {
  const [results, setResults] = useState<ResumeResults>({ selected: [], rejected: [], considered: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [expandedResumes, setExpandedResumes] = useState<Set<string>>(new Set());
  const [gridColumns, setGridColumns] = useState<string>('repeat(auto-fit, minmax(400px, 1fr))');
  const [uploadMetadata, setUploadMetadata] = useState<{
    total_uploaded: number;
    job_description: string;
    processed_at: string;
    user_id?: string;
    tokens_used?: number;
  } | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showContactInfo, setShowContactInfo] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'carousel'>('carousel');
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [showResumeModal, setShowResumeModal] = useState(false);
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  // Helper function to get all contact information from resumes
  const getAllContactInfo = () => {
    const allResumes = [...results.selected, ...results.rejected, ...results.considered];
    return allResumes.map(resume => ({
      id: resume.id,
      name: resume.name || 'Unknown',
      email: resume.email || 'No email provided',
      category: resume.category,
      score: resume.score
    }));
  };

  // Helper function to calculate total resumes
  const getTotalResumes = () => {
    return results.selected.length + results.rejected.length + results.considered.length;
  };

  // Helper function to extract job title from job description
  const extractJobTitle = (jobDescription: string): string => {
    if (!jobDescription || typeof jobDescription !== 'string') {
      return 'Unknown Position';
    }

    // Look for common job title patterns
    const titlePatterns = [
      /Job Title:\s*([^\n\r]+)/i,
      /Position:\s*([^\n\r]+)/i,
      /Role:\s*([^\n\r]+)/i,
      /Title:\s*([^\n\r]+)/i,
      /We are seeking a\s+([^,]+)/i,
      /Looking for a\s+([^,]+)/i,
      /Seeking a\s+([^,]+)/i
    ];

    for (const pattern of titlePatterns) {
      const match = jobDescription.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    // If no pattern matches, try to extract from the first line
    const firstLine = jobDescription.split('\n')[0].trim();
    if (firstLine.length > 0 && firstLine.length < 100) {
      return firstLine;
    }

    return 'Unknown Position';
  };

  // Helper function to extract key skills/tags from resume content
  const extractKeyTags = (content: string | undefined | null): string[] => {
    // Handle undefined, null, or empty content
    if (!content || typeof content !== 'string') {
      return [];
    }

    const skills = [
      'Python', 'JavaScript', 'React', 'Node.js', 'Django', 'Flask', 'SQL', 'MongoDB',
      'AWS', 'Docker', 'Kubernetes', 'Git', 'Machine Learning', 'AI', 'Data Science',
      'Frontend', 'Backend', 'Full Stack', 'DevOps', 'Cloud', 'API', 'Database',
      'Java', 'C++', 'TypeScript', 'Vue.js', 'Angular', 'Express', 'Spring',
      'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch', 'GraphQL', 'REST'
    ];

    const foundSkills = skills.filter(skill =>
      content.toLowerCase().includes(skill.toLowerCase())
    );

    return foundSkills.slice(0, 3); // Limit to 3 most relevant tags
  };


  // Helper function to truncate text
  const truncateText = (text: string, maxLength: number = 120): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // Toggle expanded state for resume details
  const toggleExpanded = (resumeId: string) => {
    setExpandedResumes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(resumeId)) {
        newSet.delete(resumeId);
      } else {
        newSet.add(resumeId);
      }
      return newSet;
    });
  };

  const handleViewResume = (resume: Resume) => {
    setSelectedResume(resume);
    setShowResumeModal(true);
  };

  const closeResumeModal = () => {
    setShowResumeModal(false);
    setSelectedResume(null);
  };

  // Calculate optimal grid layout based on number of resumes
  const calculateGridLayout = (totalResumes: number) => {
    if (totalResumes <= 4) {
      return 'repeat(2, 1fr)';
    } else if (totalResumes <= 8) {
      return 'repeat(3, 1fr)';
    } else if (totalResumes <= 12) {
      return 'repeat(4, 1fr)';
    } else if (totalResumes <= 20) {
      return 'repeat(5, 1fr)';
    } else {
      return 'repeat(6, 1fr)';
    }
  };

  useEffect(() => {
    const storedResults = localStorage.getItem('resumeResults');
    if (storedResults) {
      try {
        const parsedResults = JSON.parse(storedResults);
        // Ensure the results have the expected structure
        const newResults = {
          selected: parsedResults.selected || [],
          rejected: parsedResults.rejected || [],
          considered: parsedResults.considered || []
        };
        
        // Debug logging
        console.log('Parsed results from localStorage:', parsedResults);
        console.log('Selected resumes:', newResults.selected);
        if (newResults.selected.length > 0) {
          console.log('First selected resume:', newResults.selected[0]);
          console.log('First selected resume s3_url:', newResults.selected[0].s3_url);
          console.log('First selected resume keys:', Object.keys(newResults.selected[0]));
        }
        
        setResults(newResults);
        
        // Extract and store metadata
        console.log('Parsed results:', parsedResults);
        if (parsedResults.metadata) {
          console.log('Metadata found:', parsedResults.metadata);
          setUploadMetadata(parsedResults.metadata);
        } else {
          console.log('No metadata found in parsed results');
        }
        
        // Calculate total resumes and update grid layout
        const totalResumes = newResults.selected.length + newResults.rejected.length + newResults.considered.length;
        setGridColumns(calculateGridLayout(totalResumes));
      } catch (error) {
        console.error('Error parsing stored results:', error);
        setResults({ selected: [], rejected: [], considered: [] });
      }
    }
    setIsLoading(false);
  }, []);


  const moveResume = (resumeId: string, fromCategory: string, toCategory: string) => {
    setResults(prev => {
      const newResults = { ...prev };
      const resume = newResults[fromCategory as keyof ResumeResults].find(r => r.id === resumeId);
      if (resume) {
        resume.category = toCategory as 'selected' | 'rejected' | 'considered';
        newResults[fromCategory as keyof ResumeResults] = newResults[fromCategory as keyof ResumeResults].filter(r => r.id !== resumeId);
        newResults[toCategory as keyof ResumeResults].push(resume);
        
        // Recalculate grid layout
        const totalResumes = newResults.selected.length + newResults.rejected.length + newResults.considered.length;
        setGridColumns(calculateGridLayout(totalResumes));
      }
      return newResults;
    });
  };


  const getCategoryStats = (category: string) => {
    const count = results[category as keyof ResumeResults].length;
    return `${count} resume${count !== 1 ? 's' : ''}`;
  };

  if (isLoading) {
    return <div className="loading">Loading results...</div>;
  }

  return (
    <div className="results-container">
        <div className="results-header">
          <div className="header-left">
            <h1 className="results-title">Resume Shortlisting Results</h1>
          </div>
          <div className="header-actions">
            <div className="view-mode-toggle">
              <button 
                className={`btn ${viewMode === 'carousel' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setViewMode('carousel')}
              >
                Carousel
              </button>
              <button 
                className={`btn ${viewMode === 'list' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setViewMode('list')}
              >
                List
              </button>
            </div>
            <button 
              className="btn btn-primary" 
              onClick={() => setShowContactInfo(!showContactInfo)}
            >
              {showContactInfo ? 'Hide' : 'Show'} Contact Info
            </button>
          </div>
        </div>



      {/* Contact Information Section */}
      {showContactInfo && (
        <div className="contact-info-section">
          <div className="contact-info-card">
            <div className="contact-info-header">
              <h3>Contact Information</h3>
              <p>All candidate names and email addresses from the uploaded resumes</p>
            </div>
            <div className="contact-info-content">
              <div className="contact-info-grid">
                {getAllContactInfo().map((contact, index) => (
                  <div key={contact.id} className="contact-info-item">
                    <div className="contact-info-details">
                      <div className="contact-name">{contact.name}</div>
                      <div className="contact-email">{contact.email}</div>
                      <div className="contact-category">
                        <span className={`category-badge category-${contact.category}`}>
                          {contact.category}
                        </span>
                        <span className="contact-score">
                          Score: {contact.score ? contact.score.toFixed(1) : '0.0'}/10
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Resume Results - Carousel or List View */}
      {viewMode === 'carousel' ? (
        <>
          {/* Selected Resumes Carousel */}
          {results.selected.length > 0 && (
            <div className="carousel-section">
              <div className="carousel-section-header">
                <h3>Selected Candidates</h3>
              </div>
              <ResumeCarousel 
                resumes={results.selected}
                category="Selected"
                onResumeClick={(resume) => {
                  console.log('Selected resume:', resume);
                  console.log('Resume s3_url:', resume.s3_url);
                }}
              />
            </div>
          )}

          {/* Considered Resumes Carousel */}
          {results.considered.length > 0 && (
            <div className="carousel-section">
              <div className="carousel-section-header">
                <h3>Can Be Considered</h3>
              </div>
              <ResumeCarousel 
                resumes={results.considered}
                category="Considered"
                onResumeClick={(resume) => console.log('Considered resume:', resume)}
              />
            </div>
          )}

          {/* Rejected Resumes Carousel */}
          {results.rejected.length > 0 && (
            <div className="carousel-section">
              <div className="carousel-section-header">
                <h3>Rejected Candidates</h3>
              </div>
              <ResumeCarousel 
                resumes={results.rejected}
                category="Rejected"
                onResumeClick={(resume) => console.log('Rejected resume:', resume)}
              />
            </div>
          )}
        </>
      ) : (
        <>
          {/* Selected Section */}
      <div className="category-section">
        <div className="category-header category-selected">
          <div className="category-title">Selected Resumes</div>
          <div className="category-count">{getCategoryStats('selected')}</div>
        </div>
        <div className="category-content">
          <div className="resume-list" style={{ gridTemplateColumns: gridColumns }}>
            {results.selected.filter(resume => resume && resume.id).map(resume => (
              <div key={resume.id} className={`resume-list-item ${expandedResumes.has(resume.id) ? 'expanded' : ''}`}>
                <div className="resume-list-main" onClick={() => toggleExpanded(resume.id)}>
                  <div className="resume-list-info">
                    <div className="resume-list-name">{resume.name || 'Unknown'}</div>
                    <div className="resume-list-email">{resume.email || 'No email provided'}</div>
                    <div className="resume-list-score">
                      Score: {resume.score ? resume.score.toFixed(1) : '0.0'}/10
                    </div>
                  </div>
                  <div className="resume-list-actions">
                    <button 
                      className="btn btn-sm btn-primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewResume(resume);
                      }}
                    >
                      View Resume
                    </button>
                    <button 
                      className="btn btn-sm btn-warning"
                      onClick={() => moveResume(resume.id, 'selected', 'considered')}
                    >
                      Move to Considered
                    </button>
                    <button 
                      className="btn btn-sm btn-danger"
                      onClick={() => moveResume(resume.id, 'selected', 'rejected')}
                    >
                      Move to Rejected
                    </button>
                  </div>
                </div>
                <div className={`resume-list-hover ${expandedResumes.has(resume.id) ? 'expanded' : ''}`}>
                  <div className="resume-list-details">
                    <div className="resume-list-skills">
                      <strong>Skills:</strong>
                      {resume.strengths && resume.strengths.length > 0 ? (
                        resume.strengths.slice(0, 3).map((strength: string, idx: number) => (
                          <span key={idx} className="skill-tag">{strength}</span>
                        ))
                      ) : (
                        <span className="skill-tag">No skills identified</span>
                      )}
                    </div>
                    <div className="resume-list-explanation">
                      <strong>Analysis:</strong> 
                      {resume.explanation && resume.explanation.length > 200 ? (
                        <div>
                          {expandedResumes.has(resume.id) 
                            ? resume.explanation 
                            : resume.explanation.substring(0, 200) + '...'
                          }
                          <button 
                            className="read-more-btn"
                            onClick={() => toggleExpanded(resume.id)}
                          >
                            {expandedResumes.has(resume.id) ? 'Show Less' : 'Read More'}
                          </button>
                        </div>
                      ) : (
                        resume.explanation || 'No explanation provided'
                      )}
                    </div>
                    {resume.weaknesses && resume.weaknesses.length > 0 && (
                      <div className="resume-list-weaknesses">
                        <strong>Areas for Improvement:</strong>
                        {resume.weaknesses.slice(0, 2).map((weakness: string, idx: number) => (
                          <span key={idx} className="weakness-tag">{weakness}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Considered Section */}
      <div className="category-section">
        <div className="category-header category-considered">
          <div className="category-title">Can Be Considered</div>
          <div className="category-count">{getCategoryStats('considered')}</div>
        </div>
        <div className="category-content">
          <div className="resume-list" style={{ gridTemplateColumns: gridColumns }}>
            {results.considered.filter(resume => resume && resume.id).map(resume => (
              <div key={resume.id} className={`resume-list-item ${expandedResumes.has(resume.id) ? 'expanded' : ''}`}>
                <div className="resume-list-main" onClick={() => toggleExpanded(resume.id)}>
                  <div className="resume-list-info">
                    <div className="resume-list-name">{resume.name || 'Unknown'}</div>
                    <div className="resume-list-email">{resume.email || 'No email provided'}</div>
                    <div className="resume-list-score">
                      Score: {resume.score ? resume.score.toFixed(1) : '0.0'}/10
                    </div>
                  </div>
                  <div className="resume-list-actions">
                    <button 
                      className="btn btn-sm btn-primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewResume(resume);
                      }}
                    >
                      View Resume
                    </button>
                    <button 
                      className="btn btn-sm btn-success"
                      onClick={() => moveResume(resume.id, 'considered', 'selected')}
                    >
                      Move to Selected
                    </button>
                    <button 
                      className="btn btn-sm btn-danger"
                      onClick={() => moveResume(resume.id, 'considered', 'rejected')}
                    >
                      Move to Rejected
                    </button>
                  </div>
                </div>
                <div className={`resume-list-hover ${expandedResumes.has(resume.id) ? 'expanded' : ''}`}>
                  <div className="resume-list-details">
                    <div className="resume-list-skills">
                      <strong>Skills:</strong>
                      {resume.strengths && resume.strengths.length > 0 ? (
                        resume.strengths.slice(0, 3).map((strength: string, idx: number) => (
                          <span key={idx} className="skill-tag">{strength}</span>
                        ))
                      ) : (
                        <span className="skill-tag">No skills identified</span>
                      )}
                    </div>
                    <div className="resume-list-explanation">
                      <strong>Analysis:</strong> 
                      {resume.explanation && resume.explanation.length > 200 ? (
                        <div>
                          {expandedResumes.has(resume.id) 
                            ? resume.explanation 
                            : resume.explanation.substring(0, 200) + '...'
                          }
                          <button 
                            className="read-more-btn"
                            onClick={() => toggleExpanded(resume.id)}
                          >
                            {expandedResumes.has(resume.id) ? 'Show Less' : 'Read More'}
                          </button>
                        </div>
                      ) : (
                        resume.explanation || 'No explanation provided'
                      )}
                    </div>
                    {resume.weaknesses && resume.weaknesses.length > 0 && (
                      <div className="resume-list-weaknesses">
                        <strong>Areas for Improvement:</strong>
                        {resume.weaknesses.slice(0, 2).map((weakness: string, idx: number) => (
                          <span key={idx} className="weakness-tag">{weakness}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Rejected Section */}
      <div className="category-section">
        <div className="category-header category-rejected">
          <div className="category-title">Rejected Resumes</div>
          <div className="category-count">{getCategoryStats('rejected')}</div>
        </div>
        <div className="category-content">
          <div className="resume-list" style={{ gridTemplateColumns: gridColumns }}>
            {results.rejected.filter(resume => resume && resume.id).map(resume => (
              <div key={resume.id} className={`resume-list-item ${expandedResumes.has(resume.id) ? 'expanded' : ''}`}>
                <div className="resume-list-main" onClick={() => toggleExpanded(resume.id)}>
                  <div className="resume-list-info">
                    <div className="resume-list-name">{resume.name || 'Unknown'}</div>
                    <div className="resume-list-email">{resume.email || 'No email provided'}</div>
                    <div className="resume-list-score">
                      Score: {resume.score ? resume.score.toFixed(1) : '0.0'}/10
                    </div>
                  </div>
                  <div className="resume-list-actions">
                    <button 
                      className="btn btn-sm btn-primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewResume(resume);
                      }}
                    >
                      View Resume
                    </button>
                    <button 
                      className="btn btn-sm btn-success"
                      onClick={() => moveResume(resume.id, 'rejected', 'selected')}
                    >
                      Move to Selected
                    </button>
                    <button 
                      className="btn btn-sm btn-warning"
                      onClick={() => moveResume(resume.id, 'rejected', 'considered')}
                    >
                      Move to Considered
                    </button>
                  </div>
                </div>
                <div className={`resume-list-hover ${expandedResumes.has(resume.id) ? 'expanded' : ''}`}>
                  <div className="resume-list-details">
                    <div className="resume-list-skills">
                      <strong>Skills:</strong>
                      {resume.strengths && resume.strengths.length > 0 ? (
                        resume.strengths.slice(0, 3).map((strength: string, idx: number) => (
                          <span key={idx} className="skill-tag">{strength}</span>
                        ))
                      ) : (
                        <span className="skill-tag">No skills identified</span>
                      )}
                    </div>
                    <div className="resume-list-explanation">
                      <strong>Analysis:</strong> 
                      {resume.explanation && resume.explanation.length > 200 ? (
                        <div>
                          {expandedResumes.has(resume.id) 
                            ? resume.explanation 
                            : resume.explanation.substring(0, 200) + '...'
                          }
                          <button 
                            className="read-more-btn"
                            onClick={() => toggleExpanded(resume.id)}
                          >
                            {expandedResumes.has(resume.id) ? 'Show Less' : 'Read More'}
                          </button>
                        </div>
                      ) : (
                        resume.explanation || 'No explanation provided'
                      )}
                    </div>
                    {resume.weaknesses && resume.weaknesses.length > 0 && (
                      <div className="resume-list-weaknesses">
                        <strong>Areas for Improvement:</strong>
                        {resume.weaknesses.slice(0, 2).map((weakness: string, idx: number) => (
                          <span key={idx} className="weakness-tag">{weakness}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
        </>
      )}

      
      <BackToTop />
      <ConfettiEffect 
        trigger={showConfetti} 
        onComplete={() => setShowConfetti(false)} 
      />
      
      {/* Resume Modal */}
      {showResumeModal && selectedResume && (
        <div className="modal-overlay" onClick={closeResumeModal}>
          <div className="resume-modal" onClick={(e) => e.stopPropagation()}>
            <div className="resume-modal-header">
              <h2>Resume: {selectedResume.name || 'Unknown'}</h2>
              <button className="modal-close-btn" onClick={closeResumeModal}>
                ✕
              </button>
            </div>
            <div className="resume-modal-content">
              <div className="resume-info">
                <div className="resume-info-item">
                  <strong>Name:</strong> {selectedResume.name || 'Unknown'}
                </div>
                <div className="resume-info-item">
                  <strong>Email:</strong> {selectedResume.email || 'No email provided'}
                </div>
                <div className="resume-info-item">
                  <strong>Score:</strong> {selectedResume.score ? selectedResume.score.toFixed(1) : '0.0'}/10
                </div>
                <div className="resume-info-item">
                  <strong>Category:</strong> 
                  <span className={`category-badge category-${selectedResume.category}`}>
                    {selectedResume.category.charAt(0).toUpperCase() + selectedResume.category.slice(1)}
                  </span>
                </div>
              </div>
              
              {/* S3 Link to view original resume */}
              {selectedResume.s3_url && (
                <div className="resume-s3-link">
                  <a 
                    href={selectedResume.s3_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                  >
                    📄 View Original Resume File
                  </a>
                </div>
              )}
              
              {selectedResume.explanation && (
                <div className="resume-analysis">
                  <h3>Analysis:</h3>
                  <div className="analysis-text">
                    {selectedResume.explanation}
                  </div>
                </div>
              )}
              
              {selectedResume.strengths && selectedResume.strengths.length > 0 && (
                <div className="resume-strengths">
                  <h3>Strengths:</h3>
                  <ul>
                    {selectedResume.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {selectedResume.weaknesses && selectedResume.weaknesses.length > 0 && (
                <div className="resume-weaknesses">
                  <h3>Areas for Improvement:</h3>
                  <ul>
                    {selectedResume.weaknesses.map((weakness, index) => (
                      <li key={index}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsPage;

