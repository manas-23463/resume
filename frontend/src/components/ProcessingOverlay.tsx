import React, { useState, useEffect } from 'react';
import type { ProcessedResumeFile } from '../types';

interface ProcessingOverlayProps {
  isVisible: boolean;
  resumeCount: number;
  resumeFiles?: ProcessedResumeFile[];
}

const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({ isVisible, resumeCount, resumeFiles = [] }) => {
  const [currentStage, setCurrentStage] = useState(0);
  const [currentResumeIndex, setCurrentResumeIndex] = useState(0);
  
  // Force re-render when resumeCount changes
  useEffect(() => {
    // Component will re-render when resumeCount changes
  }, [resumeCount]);
  
  const stages = [
    { icon: '📄', text: 'Reading Documents' },
    { icon: '🔍', text: 'Extracting Information' },
    { icon: '🤖', text: 'AI Analysis' },
    { icon: '📊', text: 'Generating Results' }
  ];

  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setCurrentStage(prev => {
        const nextStage = (prev + 1) % stages.length;
        
        // When we complete a full cycle (all stages), move to next resume
        if (nextStage === 0 && resumeFiles.length > 0) {
          setCurrentResumeIndex(prevIndex => {
            const nextIndex = (prevIndex + 1) % resumeFiles.length;
            return nextIndex;
          });
        }
        
        return nextStage;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isVisible, stages.length, resumeFiles]);

  if (!isVisible) return null;

  return (
    <div className="processing-overlay">
      <div className="processing-container">
        <div className="processing-animation">
          <div className="processing-spinner">
            <div className="spinner-ring"></div>
            <div className="spinner-ring"></div>
            <div className="spinner-ring"></div>
          </div>
          <div className="processing-documents">
            <div className="document-stack">
              <div className="document document-1">📄</div>
              <div className="document document-2">📄</div>
              <div className="document document-3">📄</div>
              <div className="document document-4">📄</div>
            </div>
          </div>
        </div>
        
        <div className="processing-content">
          <h2 className="processing-title">Processing Resumes</h2>
          <p className="processing-subtitle">
            Analyzing {resumeCount || 0} resume{(resumeCount || 0) !== 1 ? 's' : ''} with AI...
          </p>
          
          <div className="processing-stages">
            {stages.map((stage, index) => (
              <div 
                key={index} 
                className={`stage ${index === currentStage ? 'active' : ''}`}
              >
                <div className="stage-icon">{stage.icon}</div>
                <div className="stage-text">{stage.text}</div>
              </div>
            ))}
          </div>

          {/* Current Resume Being Processed */}
          {resumeFiles.length > 0 && (
            <div className="current-resume-section">
              <div className="current-resume-header">
                <h3>Currently Processing</h3>
                <div className="resume-counter">
                  {currentResumeIndex + 1} of {resumeFiles.length}
                </div>
              </div>
              <div className="current-resume-info">
                <div className="resume-name">
                  {resumeFiles[currentResumeIndex]?.name || 'Processing...'}
                </div>
              </div>
              
              {/* Progress for current resume */}
              <div className="resume-progress">
                <div className="resume-progress-bar">
                  <div 
                    className="resume-progress-fill"
                    style={{ 
                      width: `${((currentStage + 1) / stages.length) * 100}%` 
                    }}
                  ></div>
                </div>
                <div className="resume-progress-text">
                  {stages[currentStage]?.text}...
                </div>
              </div>
            </div>
          )}

          
          <div className="processing-progress">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            <div className="progress-text">Please wait while we analyze your resumes...</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessingOverlay;
