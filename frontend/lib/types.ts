export type JobStatus = 'queued' | 'started' | 'finished' | 'failed';

export interface Job {
  job_id: string;
  status: JobStatus;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  progress: number;
  message?: string;
  result_url?: string;
}

export interface ExtractOptions {
  format: 'markdown' | 'json' | 'text';
  normalize: boolean;
  include_metadata: boolean;
  structured: boolean;
  indexed: boolean;
  analyze_images: boolean;
}

export interface PDFInfo {
  filename: string;
  pages: number;
  size_bytes: number;
  has_tables: boolean;
  metadata: Record<string, string>;
  document_type?: string;
}

export interface TableData {
  page: number;
  index: number;
  rows: number;
  cols: number;
  data: string[][];
}

export interface BatchJob {
  batch_id: string;
  jobs: Job[];
  total: number;
  completed: number;
  failed: number;
}
