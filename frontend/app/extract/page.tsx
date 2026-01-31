'use client';

import { useState } from 'react';
import { PDFDropzone } from '@/components/pdf-dropzone';
import { ProcessingOptions } from '@/components/processing-options';
import { JobCard } from '@/components/job-card';
import { MarkdownViewer } from '@/components/markdown-viewer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useExtract, useJob, useJobResult } from '@/lib/queries';
import type { ExtractOptions } from '@/lib/types';
import { FileText, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const defaultOptions: ExtractOptions = {
  format: 'markdown',
  normalize: true,
  include_metadata: true,
  structured: false,
  indexed: false,
  analyze_images: false,
};

export default function ExtractPage() {
  const [file, setFile] = useState<File | null>(null);
  const [options, setOptions] = useState<ExtractOptions>(defaultOptions);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const extractMutation = useExtract();
  const { data: job } = useJob(currentJobId);
  const { data: result } = useJobResult(
    currentJobId,
    job?.status === 'finished'
  );

  const isProcessing = extractMutation.isPending || (job && job.status !== 'finished' && job.status !== 'failed');

  const handleExtract = async () => {
    if (!file) {
      toast.error('Selecione um arquivo PDF');
      return;
    }

    try {
      const response = await extractMutation.mutateAsync({ file, options });
      setCurrentJobId(response.job_id);
      toast.success('Extração iniciada!');
    } catch (error) {
      toast.error('Erro ao iniciar extração');
      console.error(error);
    }
  };

  const handleClear = () => {
    setFile(null);
    setCurrentJobId(null);
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file?.name.replace('.pdf', '.md') || 'resultado.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <FileText className="h-8 w-8" />
          Extrair PDF
        </h1>
        <p className="text-muted-foreground mt-2">
          Extraia texto estruturado de documentos PDF jurídicos
        </p>
      </div>

      <div className="grid gap-6">
        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Arquivo</CardTitle>
            <CardDescription>Selecione o PDF para extração</CardDescription>
          </CardHeader>
          <CardContent>
            <PDFDropzone
              onFileSelect={setFile}
              selectedFile={file}
              onClear={handleClear}
              disabled={isProcessing}
            />
          </CardContent>
        </Card>

        {/* Options Section */}
        <Card>
          <CardHeader>
            <CardTitle>Opções de Processamento</CardTitle>
            <CardDescription>Configure como o documento será processado</CardDescription>
          </CardHeader>
          <CardContent>
            <ProcessingOptions
              options={options}
              onChange={setOptions}
              disabled={isProcessing}
            />
          </CardContent>
        </Card>

        {/* Extract Button */}
        <Button
          size="lg"
          onClick={handleExtract}
          disabled={!file || isProcessing}
          className="w-full"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Processando...
            </>
          ) : (
            <>
              <FileText className="h-5 w-5 mr-2" />
              Extrair Texto
            </>
          )}
        </Button>

        {/* Job Status */}
        {job && (
          <JobCard
            job={job}
            onViewResult={() => {}}
            onDownload={handleDownload}
          />
        )}

        {/* Result */}
        {result && job?.status === 'finished' && (
          <MarkdownViewer
            content={result}
            filename={file?.name.replace('.pdf', '.md')}
            title="Texto Extraído"
          />
        )}
      </div>
    </div>
  );
}
