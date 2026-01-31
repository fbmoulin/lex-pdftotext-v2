'use client';

import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Combine, Upload, X, Loader2, GripVertical } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useMerge, useJob, useJobResult } from '@/lib/queries';
import { JobCard } from '@/components/job-card';
import { MarkdownViewer } from '@/components/markdown-viewer';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export default function MergePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [processNumber, setProcessNumber] = useState('');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const mergeMutation = useMerge();
  const { data: job } = useJob(currentJobId);
  const { data: result } = useJobResult(currentJobId, job?.status === 'finished');

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      setFiles((prev) => [...prev, ...acceptedFiles]);
    },
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const moveFile = (from: number, to: number) => {
    setFiles((prev) => {
      const newFiles = [...prev];
      const [moved] = newFiles.splice(from, 1);
      newFiles.splice(to, 0, moved);
      return newFiles;
    });
  };

  const handleMerge = async () => {
    if (files.length < 2) {
      toast.error('Selecione pelo menos 2 arquivos para mesclar');
      return;
    }

    try {
      const response = await mergeMutation.mutateAsync({
        files,
        processNumber: processNumber || undefined,
      });
      setCurrentJobId(response.job_id);
      toast.success('Mesclagem iniciada!');
    } catch (error) {
      toast.error('Erro ao iniciar mesclagem');
      console.error(error);
    }
  };

  const isProcessing = mergeMutation.isPending || (job && job.status !== 'finished' && job.status !== 'failed');

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Combine className="h-8 w-8" />
          Mesclar PDFs
        </h1>
        <p className="text-muted-foreground mt-2">
          Combine múltiplos PDFs em um único documento
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Arquivos para Mesclar</CardTitle>
            <CardDescription>
              Arraste para reordenar. A ordem aqui será a ordem no documento final.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50',
                isProcessing && 'opacity-50 cursor-not-allowed'
              )}
            >
              <input {...getInputProps()} disabled={isProcessing} />
              <Upload className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
              <p className="font-medium">Arraste PDFs aqui ou clique para selecionar</p>
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex items-center gap-1">
                      {index > 0 && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => moveFile(index, index - 1)}
                        >
                          ↑
                        </Button>
                      )}
                      {index < files.length - 1 && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => moveFile(index, index + 1)}
                        >
                          ↓
                        </Button>
                      )}
                    </div>
                    <span className="text-sm text-muted-foreground w-6">{index + 1}.</span>
                    <span className="flex-1 truncate">{file.name}</span>
                    <Button variant="ghost" size="icon" onClick={() => removeFile(index)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Número do Processo (opcional)</CardTitle>
            <CardDescription>
              Se informado, será incluído no cabeçalho do documento mesclado
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="0000000-00.0000.0.00.0000"
              value={processNumber}
              onChange={(e) => setProcessNumber(e.target.value)}
              disabled={isProcessing}
            />
          </CardContent>
        </Card>

        <Button
          size="lg"
          onClick={handleMerge}
          disabled={files.length < 2 || isProcessing}
          className="w-full"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Mesclando...
            </>
          ) : (
            <>
              <Combine className="h-5 w-5 mr-2" />
              Mesclar {files.length} arquivo(s)
            </>
          )}
        </Button>

        {job && <JobCard job={job} />}

        {result && job?.status === 'finished' && (
          <MarkdownViewer content={result} title="Documento Mesclado" />
        )}
      </div>
    </div>
  );
}
