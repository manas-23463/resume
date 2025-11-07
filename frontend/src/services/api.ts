import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to handle file uploads
api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    config.headers['Content-Type'] = 'multipart/form-data';
  }
  return config;
});

export const uploadResumes = async (formData: FormData) => {
  const response = await api.post('/upload', formData);
  return response.data;
};

export const processResumes = async (formData: FormData) => {
  const response = await api.post('/process', formData);
  return response.data;
};

export const getProcessStatus = async (taskId: string) => {
  const response = await api.get(`/process/status/${taskId}`);
  return response.data;
};


export const storeResumeData = async (userId: string, resumeData: any[]) => {
  const response = await api.post('/store-resume-data', {
    user_id: userId,
    resume_data: resumeData
  });
  return response.data;
};

export const getUserResumeData = async (userId: string, limit: number = 100) => {
  const response = await api.get(`/user-resume-data/${userId}?limit=${limit}`);
  return response.data;
};

export const getUserStats = async (userId: string) => {
  const response = await api.get(`/user-stats/${userId}`);
  return response.data;
};

export const updateResumeCategory = async (resumeId: string, category: string) => {
  const response = await api.put(`/update-resume-category/${resumeId}?category=${category}`);
  return response.data;
};

// Authentication API calls
export const registerUser = async (email: string, password: string, displayName: string, phoneNumber?: string) => {
  const response = await api.post('/auth/register', {
    email,
    password,
    displayName,
    phoneNumber: phoneNumber || null
  });
  return response.data;
};

export const loginUser = async (email: string, password: string) => {
  const response = await api.post('/auth/login', {
    email,
    password
  });
  return response.data;
};

export const getUserProfile = async (userId: string) => {
  const response = await api.get(`/auth/user/${userId}`);
  return response.data;
};

export const updateUserProfile = async (userId: string, profileData: any) => {
  const response = await api.put(`/auth/user/${userId}`, profileData);
  return response.data;
};

// Token Management API calls
export const getUserTokens = async (userId: string) => {
  const response = await api.get(`/tokens/${userId}`);
  return response.data;
};

export const initializeUserTokens = async (userId: string) => {
  const response = await api.post(`/tokens/initialize/${userId}`);
  return response.data;
};

export const purchaseTokens = async (userId: string, tokenPackage: string, paymentMethod: string) => {
  const response = await api.post('/tokens/purchase', {
    user_id: userId,
    token_package: tokenPackage,
    payment_method: paymentMethod
  });
  return response.data;
};

// Uploaded Files API calls
export const getUserUploadedFiles = async (userId: string, limit: number = 100) => {
  const response = await api.get(`/user-uploaded-files/${userId}?limit=${limit}`);
  return response.data;
};

export const deleteUploadedFile = async (fileId: string) => {
  const response = await api.delete(`/uploaded-file/${fileId}`);
  return response.data;
};

export default api;
