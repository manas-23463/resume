import React, { useState } from 'react';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="auth-page">
      <div className="auth-header">
        <h1 className="auth-main-title">Resume Shortlisting System</h1>
        <p className="auth-subtitle">Sign in to your account or create a new one</p>
      </div>
      
      <div className="auth-toggle">
        <button
          className={`auth-toggle-btn ${isLogin ? 'active' : ''}`}
          onClick={() => setIsLogin(true)}
        >
          Sign In
        </button>
        <button
          className={`auth-toggle-btn ${!isLogin ? 'active' : ''}`}
          onClick={() => setIsLogin(false)}
        >
          Sign Up
        </button>
      </div>

      {isLogin ? <LoginForm /> : <SignupForm />}
    </div>
  );
};

export default AuthPage;
