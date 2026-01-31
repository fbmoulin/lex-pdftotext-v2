'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Download, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';

interface MarkdownViewerProps {
  content: string;
  filename?: string;
  title?: string;
}

export function MarkdownViewer({ content, filename = 'resultado.md', title = 'Resultado' }: MarkdownViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    toast.success('Conteúdo copiado!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Download iniciado!');
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            <span className="ml-2 hidden sm:inline">{copied ? 'Copiado!' : 'Copiar'}</span>
          </Button>
          <Button size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4" />
            <span className="ml-2 hidden sm:inline">Download</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm dark:prose-invert max-w-none overflow-auto max-h-[600px] p-4 bg-muted/50 rounded-lg">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
              h2: ({ children }) => <h2 className="text-lg font-semibold mt-3 mb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-base font-medium mt-2 mb-1">{children}</h3>,
              p: ({ children }) => <p className="my-2">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 my-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 my-2">{children}</ol>,
              li: ({ children }) => <li className="my-1">{children}</li>,
              code: ({ children }) => (
                <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>
              ),
              pre: ({ children }) => (
                <pre className="bg-muted p-3 rounded-lg overflow-x-auto my-2">{children}</pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-primary pl-4 my-2 italic">{children}</blockquote>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-2">
                  <table className="w-full border-collapse border border-border">{children}</table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border border-border bg-muted px-3 py-2 text-left font-semibold">{children}</th>
              ),
              td: ({ children }) => <td className="border border-border px-3 py-2">{children}</td>,
              hr: () => <hr className="my-4 border-border" />,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}
