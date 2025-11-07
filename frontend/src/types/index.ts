// Shared type definitions

export interface ResumeFile {
  file: File;
  id: string;
}

export interface ProcessedResumeFile {
  name: string;
  size: number;
  type: string;
  id: string;
  candidateName?: string;
}

export interface JDFile {
  file: File;
  id: string;
}

export interface Resume {
  id: string;
  name: string;
  email: string;
  content: string;
  score: number;
  category: 'selected' | 'rejected' | 'considered';
  explanation?: string;
  strengths?: string[];
  weaknesses?: string[];
  s3_url?: string;
  fileName?: string;
}

export interface ResumeResults {
  selected: Resume[];
  rejected: Resume[];
  considered: Resume[];
}

export interface TokenData {
  tokens: number;
  total_used: number;
  created_at: string;
  updated_at: string;
}
