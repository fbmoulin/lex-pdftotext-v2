'use client';

import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Files, Upload, X, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ProcessingOptions } from '@/components/processing-options';
import { useBatch } from '@/lib/queries';
import type { ExtractOptions } from '@/lib/types';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const defaultOptions: ExtractOptions = {
  format: 'markdown',
  normalize: true,
  include_metadata: true,
  structured: false,
  indexed: false,
  analyze_images: false,
};

export default function BatchPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [options, setOptions] = useState<ExtractOptions>(defaultOptions);
  const batchMutation = useBatch();

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

  const handleProcess = async () => {
    if (files.length === 0) {
      toast.error('Selecione pelo menos um arquivo');
      return;
    }

    try {
      await batchMutation.mutateAsync({ files, options });
      toast.success(`${files.length} arquivos enviados para processamento!`);
      setFiles([]);
    } catch (error) {
      toast.error('Erro ao iniciar processamento em lote');
      console.error(error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isProcessing = batchMutation.isPending;

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Files className="h-8 w-8" />
          Processamento em Lote
        </h1>
        <p className="text-muted-foreground mt-2">
          Processe múltiplos PDFs de uma vez
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Arquivos</CardTitle>
            <CardDescription>Arraste múltiplos PDFs ou clique para selecionar</CardDescription>
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
              <p className="text-sm text-muted-foreground mt-1">
                {files.length} arquivo(s) selecionado(s)
              </p>
            </div>

            {files.length > 0 && (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {files.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Files className="h-5 w-5 shrink-0 text-primary" />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{file.name}</p>
                        <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeFile(index)}
                      disabled={isProcessing}
                    >
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
            <CardTitle>Opções de Processamento</CardTitle>
          </CardHeader>
          <CardContent>
            <ProcessingOptions options={options} onChange={setOptions} disabled={isProcessing} />
          </CardContent>
        </Card>

        <Button
          size="lg"
          onClick={handleProcess}
          disabled={files.length === 0 || isProcessing}
          className="w-full"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Processando...
            </>
          ) : (
            <>
              <Files className="h-5 w-5 mr-2" />
              Processar {files.length} arquivo(s)
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
