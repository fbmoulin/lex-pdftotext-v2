'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';
import type { ExtractOptions, Job } from './types';

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data as Job | undefined;
      if (!data) return 2000;
      return data.status === 'finished' || data.status === 'failed' ? false : 2000;
    },
  });
}

export function useJobResult(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['job-result', jobId],
    queryFn: () => api.getResult(jobId!),
    enabled: !!jobId && enabled,
    staleTime: Infinity,
  });
}

export function useExtract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, options }: { file: File; options: ExtractOptions }) =>
      api.extract(file, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function usePDFInfo() {
  return useMutation({
    mutationFn: (file: File) => api.getInfo(file),
  });
}

export function useExtractTables() {
  return useMutation({
    mutationFn: ({ file, format }: { file: File; format: 'markdown' | 'csv' }) =>
      api.extractTables(file, format),
  });
}

export function useBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ files, options }: { files: File[]; options: ExtractOptions }) =>
      api.batch(files, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useMerge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ files, processNumber }: { files: File[]; processNumber?: string }) =>
      api.merge(files, processNumber),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useJobs(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['jobs', limit, offset],
    queryFn: () => api.listJobs(limit, offset),
    refetchInterval: 10000,
  });
}
