'use client';

import { useState } from 'react';
import { History, RefreshCw, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useJobs } from '@/lib/queries';
import type { JobStatus } from '@/lib/types';
import { cn } from '@/lib/utils';

const statusConfig: Record<JobStatus, { icon: React.ElementType; label: string; color: string }> = {
  queued: { icon: Clock, label: 'Na fila', color: 'text-muted-foreground' },
  started: { icon: Loader2, label: 'Processando', color: 'text-blue-500' },
  finished: { icon: CheckCircle2, label: 'Concluído', color: 'text-green-500' },
  failed: { icon: XCircle, label: 'Erro', color: 'text-red-500' },
};

export default function JobsPage() {
  const [page, setPage] = useState(0);
  const limit = 20;
  const { data: jobs, isLoading, refetch, isFetching } = useJobs(limit, page * limit);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const StatusBadge = ({ status }: { status: JobStatus }) => {
    const config = statusConfig[status];
    const Icon = config.icon;
    return (
      <div className={cn('flex items-center gap-2', config.color)}>
        <Icon className={cn('h-4 w-4', status === 'started' && 'animate-spin')} />
        <span>{config.label}</span>
      </div>
    );
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <History className="h-8 w-8" />
            Histórico de Jobs
          </h1>
          <p className="text-muted-foreground mt-2">
            Visualize o histórico de processamentos
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={cn('h-4 w-4 mr-2', isFetching && 'animate-spin')} />
          Atualizar
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : jobs && jobs.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Criado em</TableHead>
                    <TableHead>Concluído em</TableHead>
                    <TableHead>Progresso</TableHead>
                    <TableHead>Mensagem</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.job_id}>
                      <TableCell className="font-mono text-sm">{job.job_id.slice(0, 8)}...</TableCell>
                      <TableCell>
                        <StatusBadge status={job.status} />
                      </TableCell>
                      <TableCell>{formatDate(job.created_at)}</TableCell>
                      <TableCell>{job.finished_at ? formatDate(job.finished_at) : '-'}</TableCell>
                      <TableCell>{job.progress}%</TableCell>
                      <TableCell className="max-w-xs truncate">{job.message || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex items-center justify-between p-4 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Anterior
                </Button>
                <span className="text-sm text-muted-foreground">Página {page + 1}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!jobs || jobs.length < limit}
                >
                  Próxima
                </Button>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Nenhum job encontrado</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
