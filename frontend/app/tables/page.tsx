'use client';

import { useState } from 'react';
import { Table2, Loader2, Download, Copy, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PDFDropzone } from '@/components/pdf-dropzone';
import { useExtractTables } from '@/lib/queries';
import type { TableData } from '@/lib/types';
import { toast } from 'sonner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

export default function TablesPage() {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<'markdown' | 'csv'>('markdown');
  const [tables, setTables] = useState<TableData[]>([]);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const extractMutation = useExtractTables();

  const handleExtract = async () => {
    if (!file) {
      toast.error('Selecione um arquivo PDF');
      return;
    }

    try {
      const result = await extractMutation.mutateAsync({ file, format });
      setTables(result);
      if (result.length === 0) {
        toast.info('Nenhuma tabela encontrada no documento');
      } else {
        toast.success(`${result.length} tabela(s) extraída(s)!`);
      }
    } catch (error) {
      toast.error('Erro ao extrair tabelas');
      console.error(error);
    }
  };

  const formatTableAsMarkdown = (table: TableData): string => {
    if (table.data.length === 0) return '';

    const header = table.data[0];
    const rows = table.data.slice(1);

    let md = '| ' + header.join(' | ') + ' |\n';
    md += '| ' + header.map(() => '---').join(' | ') + ' |\n';
    rows.forEach((row) => {
      md += '| ' + row.join(' | ') + ' |\n';
    });

    return md;
  };

  const formatTableAsCSV = (table: TableData): string => {
    return table.data.map((row) => row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',')).join('\n');
  };

  const handleCopy = async (table: TableData, index: number) => {
    const content = format === 'markdown' ? formatTableAsMarkdown(table) : formatTableAsCSV(table);
    await navigator.clipboard.writeText(content);
    setCopiedIndex(index);
    toast.success('Tabela copiada!');
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleDownload = (table: TableData, index: number) => {
    const content = format === 'markdown' ? formatTableAsMarkdown(table) : formatTableAsCSV(table);
    const ext = format === 'markdown' ? 'md' : 'csv';
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tabela_${index + 1}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setFile(null);
    setTables([]);
  };

  const isProcessing = extractMutation.isPending;

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Table2 className="h-8 w-8" />
          Extrair Tabelas
        </h1>
        <p className="text-muted-foreground mt-2">
          Extraia tabelas de PDFs em formato Markdown ou CSV
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

        <Card>
          <CardHeader>
            <CardTitle>Formato de Saída</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={format} onValueChange={(v: 'markdown' | 'csv') => setFormat(v)} disabled={isProcessing}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="markdown">Markdown</SelectItem>
                <SelectItem value="csv">CSV</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Button
          size="lg"
          onClick={handleExtract}
          disabled={!file || isProcessing}
          className="w-full"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Extraindo...
            </>
          ) : (
            <>
              <Table2 className="h-5 w-5 mr-2" />
              Extrair Tabelas
            </>
          )}
        </Button>

        {tables.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">{tables.length} Tabela(s) Encontrada(s)</h2>
            {tables.map((table, index) => (
              <Card key={index}>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base">
                      Tabela {index + 1} - Página {table.page}
                    </CardTitle>
                    <CardDescription>
                      {table.rows} linhas × {table.cols} colunas
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleCopy(table, index)}>
                      {copiedIndex === index ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                    <Button size="sm" onClick={() => handleDownload(table, index)}>
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-sm">
                      <thead>
                        <tr>
                          {table.data[0]?.map((cell, i) => (
                            <th key={i} className="border border-border bg-muted px-3 py-2 text-left font-semibold">
                              {cell}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {table.data.slice(1).map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                              <td key={cellIndex} className="border border-border px-3 py-2">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
