import React, { createContext, useContext, useEffect, useState } from 'react';
import { registerUser, loginUser, getUserProfile, updateUserProfile as updateUserProfileAPI } from '../services/api';

interface UserProfile {
  uid: string;
  email: string;
  phoneNumber: string | null;
  displayName: string | null;
  createdAt: string;
  lastLoginAt: string;
}

interface AuthContextType {
  currentUser: UserProfile | null;
  userProfile: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, phoneNumber?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUserProfile: (data: Partial<UserProfile>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in from localStorage
    const checkAuthStatus = async () => {
      try {
        const storedUser = localStorage.getItem('currentUser');
        if (storedUser) {
          const user = JSON.parse(storedUser);
          setCurrentUser(user);
          setUserProfile(user);
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        localStorage.removeItem('currentUser');
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await loginUser(email, password);
      if (response.success) {
        const user = response.user_profile;
        setCurrentUser(user);
        setUserProfile(user);
        localStorage.setItem('currentUser', JSON.stringify(user));
      } else {
        throw new Error(response.message);
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const register = async (email: string, password: string, displayName: string, phoneNumber?: string) => {
    try {
      const response = await registerUser(email, password, displayName, phoneNumber);
      if (response.success) {
        const user = response.user_profile;
        setCurrentUser(user);
        setUserProfile(user);
        localStorage.setItem('currentUser', JSON.stringify(user));
      } else {
        throw new Error(response.message);
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const logout = async () => {
    setCurrentUser(null);
    setUserProfile(null);
    localStorage.removeItem('currentUser');
  };

  const updateUserProfile = async (data: Partial<UserProfile>) => {
    if (!currentUser) throw new Error('No user logged in');

    const cleanedData = Object.fromEntries(
      Object.entries(data).map(([key, value]) => [
        key,
        value === undefined ? null : value
      ])
    );

    const response = await updateUserProfileAPI(currentUser.uid, cleanedData);
    if (response.message) {
      const updatedProfile = { ...userProfile, ...cleanedData };
      setUserProfile(updatedProfile as UserProfile);
      localStorage.setItem('currentUser', JSON.stringify(updatedProfile));
    } else {
      throw new Error(response.message);
    }
  };

  const value = {
    currentUser,
    userProfile,
    loading,
    register,
    login,
    logout,
    updateUserProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
