'use client';

import { CheckCircle2, Clock, Loader2, XCircle, Download, Eye } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import type { Job } from '@/lib/types';
import { cn } from '@/lib/utils';

interface JobCardProps {
  job: Job;
  onViewResult?: () => void;
  onDownload?: () => void;
  compact?: boolean;
}

const statusConfig = {
  queued: {
    icon: Clock,
    label: 'Na fila',
    color: 'text-muted-foreground',
  },
  started: {
    icon: Loader2,
    label: 'Processando',
    color: 'text-blue-500',
    animate: true,
  },
  finished: {
    icon: CheckCircle2,
    label: 'Concluído',
    color: 'text-green-500',
  },
  failed: {
    icon: XCircle,
    label: 'Erro',
    color: 'text-red-500',
  },
};

export function JobCard({ job, onViewResult, onDownload, compact = false }: JobCardProps) {
  const config = statusConfig[job.status];
  const Icon = config.icon;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (compact) {
    return (
      <div className="flex items-center justify-between p-3 border rounded-lg">
        <div className="flex items-center gap-3">
          <Icon className={cn('h-5 w-5', config.color, config.animate && 'animate-spin')} />
          <div>
            <p className="font-medium text-sm">{job.job_id.slice(0, 8)}</p>
            <p className="text-xs text-muted-foreground">{config.label}</p>
          </div>
        </div>
        {job.status === 'finished' && (
          <div className="flex gap-2">
            {onViewResult && (
              <Button size="sm" variant="ghost" onClick={onViewResult}>
                <Eye className="h-4 w-4" />
              </Button>
            )}
            {onDownload && (
              <Button size="sm" variant="ghost" onClick={onDownload}>
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className={cn('h-5 w-5', config.color, config.animate && 'animate-spin')} />
          {config.label}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {(job.status === 'started' || job.status === 'queued') && (
          <Progress value={job.progress} className="h-2" />
        )}
        {job.message && (
          <p className={cn('text-sm', job.status === 'failed' ? 'text-red-500' : 'text-muted-foreground')}>
            {job.message}
          </p>
        )}
        <div className="text-xs text-muted-foreground space-y-1">
          <p>ID: {job.job_id}</p>
          <p>Criado: {formatDate(job.created_at)}</p>
          {job.finished_at && <p>Concluído: {formatDate(job.finished_at)}</p>}
        </div>
      </CardContent>
      {job.status === 'finished' && (onViewResult || onDownload) && (
        <CardFooter className="gap-2">
          {onViewResult && (
            <Button variant="outline" size="sm" onClick={onViewResult} className="flex-1">
              <Eye className="h-4 w-4 mr-2" />
              Visualizar
            </Button>
          )}
          {onDownload && (
            <Button size="sm" onClick={onDownload} className="flex-1">
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  );
}
