'use client';

import { useState } from 'react';
import { Info, Loader2, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PDFDropzone } from '@/components/pdf-dropzone';
import { usePDFInfo } from '@/lib/queries';
import type { PDFInfo } from '@/lib/types';
import { toast } from 'sonner';

export default function InfoPage() {
  const [file, setFile] = useState<File | null>(null);
  const [info, setInfo] = useState<PDFInfo | null>(null);

  const infoMutation = usePDFInfo();

  const handleAnalyze = async () => {
    if (!file) {
      toast.error('Selecione um arquivo PDF');
      return;
    }

    try {
      const result = await infoMutation.mutateAsync(file);
      setInfo(result);
      toast.success('Análise concluída!');
    } catch (error) {
      toast.error('Erro ao analisar PDF');
      console.error(error);
    }
  };

  const handleClear = () => {
    setFile(null);
    setInfo(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const isProcessing = infoMutation.isPending;

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Info className="h-8 w-8" />
          Informações do PDF
        </h1>
        <p className="text-muted-foreground mt-2">
          Visualize metadados e informações do documento sem extrair texto
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Arquivo</CardTitle>
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

        <Button
          size="lg"
          onClick={handleAnalyze}
          disabled={!file || isProcessing}
          className="w-full"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Analisando...
            </>
          ) : (
            <>
              <Info className="h-5 w-5 mr-2" />
              Analisar PDF
            </>
          )}
        </Button>

        {info && (
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Informações Gerais
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <InfoRow label="Nome do arquivo" value={info.filename} />
                <InfoRow label="Páginas" value={String(info.pages)} />
                <InfoRow label="Tamanho" value={formatFileSize(info.size_bytes)} />
                <InfoRow
                  label="Contém tabelas"
                  value={info.has_tables ? 'Sim' : 'Não'}
                />
                {info.document_type && (
                  <InfoRow label="Tipo de documento" value={info.document_type} />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Metadados do PDF</CardTitle>
              </CardHeader>
              <CardContent>
                {Object.keys(info.metadata).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(info.metadata).map(([key, value]) => (
                      <InfoRow key={key} label={key} value={value || '-'} />
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">
                    Nenhum metadado encontrado
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-start gap-4">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <span className="text-sm font-medium text-right break-all">{value}</span>
    </div>
  );
}
