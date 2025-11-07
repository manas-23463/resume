import React, { useState, useEffect } from 'react';
import type { Resume } from '../types';

interface ResumeCarouselProps {
  resumes: Resume[];
  category: string;
  onResumeClick?: (resume: Resume) => void;
}

const ResumeCarousel: React.FC<ResumeCarouselProps> = ({ resumes, category, onResumeClick }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  // Debug logging
  useEffect(() => {
    console.log(`ResumeCarousel for ${category}:`, resumes);
    if (resumes.length > 0) {
      console.log('First resume data:', resumes[0]);
      console.log('First resume s3_url:', resumes[0].s3_url);
      console.log('First resume keys:', Object.keys(resumes[0]));
      console.log('First resume s3_url type:', typeof resumes[0].s3_url);
      console.log('First resume s3_url truthy:', !!resumes[0].s3_url);
    }
  }, [resumes, category]);

  // Auto-play functionality
  useEffect(() => {
    if (isAutoPlaying && resumes.length > 1) {
      const interval = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % resumes.length);
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [isAutoPlaying, resumes.length]);

  const nextResume = () => {
    setCurrentIndex((prev) => (prev + 1) % resumes.length);
  };

  const prevResume = () => {
    setCurrentIndex((prev) => (prev - 1 + resumes.length) % resumes.length);
  };

  const goToResume = (index: number) => {
    setCurrentIndex(index);
  };

  if (resumes.length === 0) {
    return (
      <div className="carousel-container">
        <div className="carousel-empty">
          <p>No resumes in this category</p>
        </div>
      </div>
    );
  }

  const currentResume = resumes[currentIndex];

  return (
    <div className="carousel-container">
      <div className="carousel-header">
        <h3 className="carousel-title">{category} Candidates</h3>
        <div className="carousel-controls">
          <button 
            className="carousel-control-btn"
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            title={isAutoPlaying ? 'Pause auto-play' : 'Start auto-play'}
          >
            {isAutoPlaying ? '⏸️' : '▶️'}
          </button>
          <span className="carousel-counter">
            {currentIndex + 1} of {resumes.length}
          </span>
        </div>
      </div>

      <div className="carousel-wrapper">
        <button 
          className="carousel-nav carousel-nav-left"
          onClick={prevResume}
          disabled={resumes.length <= 1}
        >
          ‹
        </button>

        <div className="carousel-track">
          {resumes.map((resume, index) => {
            const isActive = index === currentIndex;
            const isPrev = index === (currentIndex - 1 + resumes.length) % resumes.length;
            const isNext = index === (currentIndex + 1) % resumes.length;
            
            return (
              <div
                key={resume.id}
                className={`carousel-card ${isActive ? 'active' : ''} ${isPrev ? 'prev' : ''} ${isNext ? 'next' : ''}`}
                onClick={() => onResumeClick?.(resume)}
              >
                <div className="card-content">
                  <div className="card-avatar">
                    <div className="avatar-circle">
                      {resume.name.charAt(0).toUpperCase()}
                    </div>
                  </div>
                  
                  <div className="card-info">
                    <h4 className="card-name">{resume.name || 'Unknown'}</h4>
                    <p className="card-email">{resume.email || 'No email provided'}</p>
                  </div>

                  <div className="card-score">
                    <div className="score-circle">
                      <span className="score-number">{resume.score.toFixed(1)}</span>
                      <span className="score-label">/10</span>
                    </div>
                  </div>
                </div>

                <div className="card-details">
                  <div className="card-category">
                    <span className={`category-badge category-${resume.category}`}>
                      {resume.category}
                    </span>
                  </div>
                  
                  {resume.strengths && resume.strengths.length > 0 && (
                    <div className="card-strengths">
                      <h5>Strengths:</h5>
                      <div className="strength-tags">
                        {resume.strengths.slice(0, 3).map((strength, idx) => (
                          <span key={idx} className="strength-tag">{strength}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {resume.explanation && (
                    <div className="card-explanation">
                      <h5>Analysis:</h5>
                      <p>{resume.explanation.substring(0, 150)}...</p>
                    </div>
                  )}

                  {/* S3 Link to view original resume - Always show for testing */}
                  <div className="card-s3-link">
                    {resume.s3_url ? (
                      <a 
                        href={resume.s3_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => e.stopPropagation()}
                      >
                        📄 View Original Resume
                      </a>
                    ) : (
                      <span className="btn btn-secondary btn-sm" style={{opacity: 0.5, cursor: 'not-allowed'}}>
                        📄 No Resume Link (s3_url: {resume.s3_url || 'undefined'})
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <button 
          className="carousel-nav carousel-nav-right"
          onClick={nextResume}
          disabled={resumes.length <= 1}
        >
          ›
        </button>
      </div>

      <div className="carousel-dots">
        {resumes.map((_, index) => (
          <button
            key={index}
            className={`carousel-dot ${index === currentIndex ? 'active' : ''}`}
            onClick={() => goToResume(index)}
          />
        ))}
      </div>
    </div>
  );
};

export default ResumeCarousel;
