import type { Job, ExtractOptions, PDFInfo, TableData, BatchJob } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  async extract(file: File, options: ExtractOptions): Promise<Job> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', options.format);
    formData.append('normalize', String(options.normalize));
    formData.append('include_metadata', String(options.include_metadata));
    formData.append('structured', String(options.structured));
    formData.append('indexed', String(options.indexed));
    formData.append('analyze_images', String(options.analyze_images));

    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<Job>(res);
  },

  async getJob(jobId: string): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    return handleResponse<Job>(res);
  },

  async getResult(jobId: string): Promise<string> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/result`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.text();
  },

  async getResultBlob(jobId: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/result`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.blob();
  },

  async getInfo(file: File): Promise<PDFInfo> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/info`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<PDFInfo>(res);
  },

  async extractTables(file: File, format: 'markdown' | 'csv' = 'markdown'): Promise<TableData[]> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);

    const res = await fetch(`${API_BASE}/tables`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<TableData[]>(res);
  },

  async batch(files: File[], options: ExtractOptions): Promise<BatchJob> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('format', options.format);
    formData.append('normalize', String(options.normalize));
    formData.append('include_metadata', String(options.include_metadata));
    formData.append('analyze_images', String(options.analyze_images));

    const res = await fetch(`${API_BASE}/batch`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<BatchJob>(res);
  },

  async merge(files: File[], processNumber?: string): Promise<Job> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    if (processNumber) {
      formData.append('process_number', processNumber);
    }

    const res = await fetch(`${API_BASE}/merge`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<Job>(res);
  },

  async listJobs(limit = 50, offset = 0): Promise<Job[]> {
    const res = await fetch(`${API_BASE}/jobs?limit=${limit}&offset=${offset}`);
    return handleResponse<Job[]>(res);
  },
};
