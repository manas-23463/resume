import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/auth');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo and Brand */}
        <div className="navbar-brand" onClick={() => navigate('/')}>
          <div className="navbar-logo">
            <img 
              src="/logo.png" 
              alt="LISA AI Logo" 
              className="logo-image"
              onError={(e) => {
                console.error('Logo failed to load:', e);
                e.currentTarget.style.display = 'none';
                const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                if (fallback) fallback.style.display = 'flex';
              }}
              onLoad={() => console.log('Logo loaded successfully')}
            />
            <div className="logo-fallback" style={{display: 'none'}}>
              <div className="logo-icon">L</div>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="navbar-nav">
          <div className="nav-links-container">
            <button 
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
              onClick={() => navigate('/')}
            >
              Upload
            </button>
            <button 
              className={`nav-link ${isActive('/results') ? 'active' : ''}`}
              onClick={() => navigate('/results')}
            >
              Results
            </button>
            <button 
              className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
              onClick={() => navigate('/dashboard')}
            >
              Dashboard
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="navbar-actions">
          {currentUser ? (
            <>
              <button className="btn-login" onClick={handleLogout}>
                Log Out
              </button>
              <button className="btn-signup" onClick={() => navigate('/dashboard')}>
                Dashboard
              </button>
            </>
          ) : (
            <>
              <button className="btn-login" onClick={() => navigate('/auth')}>
                Log In
              </button>
              <button className="btn-signup" onClick={() => navigate('/auth')}>
                Sign Up
              </button>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button 
          className="mobile-menu-btn"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          ☰
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="mobile-menu">
          <button 
            className="mobile-nav-link"
            onClick={() => {
              navigate('/');
              setIsMenuOpen(false);
            }}
          >
            Upload
          </button>
          <button 
            className="mobile-nav-link"
            onClick={() => {
              navigate('/results');
              setIsMenuOpen(false);
            }}
          >
            Results
          </button>
          <button 
            className="mobile-nav-link"
            onClick={() => {
              navigate('/dashboard');
              setIsMenuOpen(false);
            }}
          >
            Dashboard
          </button>
          <div className="mobile-actions">
            {currentUser ? (
              <button className="mobile-btn-logout" onClick={handleLogout}>
                Log Out
              </button>
            ) : (
              <>
                <button 
                  className="mobile-btn-login" 
                  onClick={() => {
                    navigate('/auth');
                    setIsMenuOpen(false);
                  }}
                >
                  Log In
                </button>
                <button 
                  className="mobile-btn-signup" 
                  onClick={() => {
                    navigate('/auth');
                    setIsMenuOpen(false);
                  }}
                >
                  Sign Up
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
