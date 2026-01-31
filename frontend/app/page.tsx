import Link from 'next/link';
import { FileText, Files, Combine, Table2, History, Info } from 'lucide-react';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const features = [
  {
    title: 'Extrair PDF',
    description: 'Extraia texto estruturado de documentos PDF jurídicos',
    icon: FileText,
    href: '/extract',
  },
  {
    title: 'Lote',
    description: 'Processe múltiplos arquivos de uma vez',
    icon: Files,
    href: '/batch',
  },
  {
    title: 'Mesclar',
    description: 'Combine PDFs por número de processo',
    icon: Combine,
    href: '/merge',
  },
  {
    title: 'Tabelas',
    description: 'Extraia tabelas em Markdown ou CSV',
    icon: Table2,
    href: '/tables',
  },
  {
    title: 'Histórico',
    description: 'Visualize jobs processados',
    icon: History,
    href: '/jobs',
  },
  {
    title: 'Info',
    description: 'Visualize metadados do PDF',
    icon: Info,
    href: '/info',
  },
];

export default function HomePage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Lex PDFtoText</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Extrator de texto para documentos jurídicos brasileiros. Converta PDFs do PJe em Markdown
          estruturado, otimizado para RAG e análise com IA.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
        {features.map((feature) => (
          <Link key={feature.href} href={feature.href}>
            <Card className="h-full hover:border-primary/50 transition-colors cursor-pointer">
              <CardHeader>
                <feature.icon className="h-10 w-10 mb-2 text-primary" />
                <CardTitle>{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      <div className="mt-12 text-center text-sm text-muted-foreground">
        <p>
          Backend API rodando em{' '}
          <code className="bg-muted px-2 py-1 rounded">
            {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </code>
        </p>
      </div>
    </div>
  );
}
