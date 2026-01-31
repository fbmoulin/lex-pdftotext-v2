'use client';

import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ExtractOptions } from '@/lib/types';

interface ProcessingOptionsProps {
  options: ExtractOptions;
  onChange: (options: ExtractOptions) => void;
  disabled?: boolean;
  showFormat?: boolean;
}

export function ProcessingOptions({
  options,
  onChange,
  disabled = false,
  showFormat = true,
}: ProcessingOptionsProps) {
  const updateOption = <K extends keyof ExtractOptions>(key: K, value: ExtractOptions[K]) => {
    onChange({ ...options, [key]: value });
  };

  return (
    <div className="space-y-4">
      {showFormat && (
        <div className="flex items-center justify-between">
          <Label htmlFor="format">Formato de saída</Label>
          <Select
            value={options.format}
            onValueChange={(value: 'markdown' | 'json' | 'text') => updateOption('format', value)}
            disabled={disabled}
          >
            <SelectTrigger className="w-[180px]" id="format">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="markdown">Markdown</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="text">Texto</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor="normalize">Normalizar texto</Label>
          <p className="text-sm text-muted-foreground">Converte MAIÚSCULAS para formato normal</p>
        </div>
        <Switch
          id="normalize"
          checked={options.normalize}
          onCheckedChange={(checked) => updateOption('normalize', checked)}
          disabled={disabled}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor="metadata">Incluir metadados</Label>
          <p className="text-sm text-muted-foreground">Extrai nº do processo, partes, advogados</p>
        </div>
        <Switch
          id="metadata"
          checked={options.include_metadata}
          onCheckedChange={(checked) => updateOption('include_metadata', checked)}
          disabled={disabled}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor="structured">Estruturar seções</Label>
          <p className="text-sm text-muted-foreground">Organiza em seções hierárquicas</p>
        </div>
        <Switch
          id="structured"
          checked={options.structured}
          onCheckedChange={(checked) => updateOption('structured', checked)}
          disabled={disabled}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor="indexed">Indexar para RAG</Label>
          <p className="text-sm text-muted-foreground">Divide em chunks otimizados para busca</p>
        </div>
        <Switch
          id="indexed"
          checked={options.indexed}
          onCheckedChange={(checked) => updateOption('indexed', checked)}
          disabled={disabled}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor="analyze_images">Analisar imagens</Label>
          <p className="text-sm text-muted-foreground">Extrai texto de imagens com IA (requer API key)</p>
        </div>
        <Switch
          id="analyze_images"
          checked={options.analyze_images}
          onCheckedChange={(checked) => updateOption('analyze_images', checked)}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
