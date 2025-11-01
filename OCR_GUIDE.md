# Guia para PDFs Escaneados (OCR)

## 🔍 Problema: PDFs Escaneados

PDFs escaneados são imagens de documentos físicos. O texto não está em formato digital, portanto ferramentas como PyMuPDF **não conseguem extrair o texto diretamente**.

### Como Identificar um PDF Escaneado?

```bash
python main.py info seu_documento.pdf
```

Se o resultado mostrar:
- **Páginas: X** mas **nenhum texto extraído** ou **muito pouco texto**
- O PDF foi provavelmente escaneado

## ✅ Solução: OCR (Optical Character Recognition)

Para processar PDFs escaneados, você precisa de **OCR** - tecnologia que "lê" texto de imagens.

### Opção 1: Tesseract OCR (Gratuito e Open Source)

#### 1. Instalar Tesseract

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por
sudo apt-get install poppler-utils  # Para converter PDF em imagens
```

**MacOS:**
```bash
brew install tesseract tesseract-lang
brew install poppler
```

**Windows:**
- Baixe: https://github.com/UB-Mannheim/tesseract/wiki
- Instale e adicione ao PATH

#### 2. Instalar Bibliotecas Python

```bash
pip install pytesseract pdf2image pillow
```

#### 3. Script para Processar PDF Escaneado

Crie um arquivo `ocr_pdf.py`:

```python
#!/usr/bin/env python3
"""
OCR para PDFs escaneados.
"""
import sys
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def extract_text_with_ocr(pdf_path, language='por'):
    """
    Extrai texto de PDF escaneado usando OCR.

    Args:
        pdf_path: Caminho do PDF
        language: Idioma do OCR ('por' para português)

    Returns:
        str: Texto extraído
    """
    print(f"📄 Convertendo PDF em imagens...")

    # Converter PDF em imagens (uma por página)
    images = convert_from_path(pdf_path, dpi=300)

    print(f"   {len(images)} páginas detectadas")
    print(f"🔍 Executando OCR...")

    all_text = []

    for i, image in enumerate(images, 1):
        print(f"   Página {i}/{len(images)}...", end='')

        # Aplicar OCR
        text = pytesseract.image_to_string(image, lang=language)
        all_text.append(text)

        print(f" ✓")

    return '\\n\\n'.join(all_text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python ocr_pdf.py <arquivo.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = Path(pdf_path).with_suffix('.txt')

    # Extrair texto
    text = extract_text_with_ocr(pdf_path, language='por')

    # Salvar
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\\n✅ Texto salvo em: {output_path}")
    print(f"   Total de caracteres: {len(text):,}")
```

#### 4. Usar o Script

```bash
python ocr_pdf.py data/input/documento_escaneado.pdf
```

Isso gera um arquivo `.txt` com o texto extraído.

#### 5. Processar o Texto Extraído

```bash
# Agora você pode usar nosso sistema normalmente
# Copie o conteúdo do .txt para um novo PDF ou processe diretamente
```

---

### Opção 2: OCRmyPDF (Automático)

**Mais fácil**: Converte PDFs escaneados em PDFs pesquisáveis.

#### 1. Instalar

```bash
pip install ocrmypdf
```

#### 2. Processar PDF

```bash
ocrmypdf --language por --deskew --clean input.pdf output_ocr.pdf
```

Isso cria `output_ocr.pdf` com texto pesquisável que nosso sistema consegue ler!

#### 3. Extrair Normalmente

```bash
python main.py extract output_ocr.pdf
```

---

### Opção 3: Serviços Cloud (Pago, mas Preciso)

Para documentos críticos ou baixa qualidade:

1. **Google Cloud Vision API**
   - Melhor precisão
   - Suporta português
   - Pago (mas tem trial gratuito)

2. **AWS Textract**
   - Focado em documentos
   - Extrai tabelas
   - Pago

3. **Azure Computer Vision**
   - OCR multilíngue
   - Boa precisão
   - Pago

---

## 🔄 Workflow Recomendado para PDFs Escaneados

```bash
# 1. Identificar se é escaneado
python main.py info documento.pdf

# 2. Se escaneado, aplicar OCR
ocrmypdf --language por --deskew documento.pdf documento_ocr.pdf

# 3. Extrair normalmente
python main.py extract documento_ocr.pdf

# 4. Ou mesclar com outros PDFs
python main.py merge data/input/ -o processo_completo.md
```

---

## 📊 Comparação de Ferramentas OCR

| Ferramenta | Custo | Precisão | Velocidade | Português |
|------------|-------|----------|------------|-----------|
| **Tesseract** | ✅ Grátis | ⭐⭐⭐ | ⚡⚡ | ✅ Sim |
| **OCRmyPDF** | ✅ Grátis | ⭐⭐⭐⭐ | ⚡⚡ | ✅ Sim |
| **Google Vision** | 💰 Pago | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | ✅ Sim |
| **AWS Textract** | 💰 Pago | ⭐⭐⭐⭐ | ⚡⚡⚡ | ✅ Sim |

---

## ⚠️ Limitações do OCR

1. **Qualidade da Imagem**: Documentos borrados ou mal escaneados = texto incorreto
2. **Formatação**: OCR pode perder formatação original
3. **Tabelas**: Difícil de manter estrutura de tabelas
4. **Assinaturas**: Não reconhece assinaturas manuscritas
5. **Tempo**: OCR é mais lento que extração de texto nativo

---

## 💡 Dicas para Melhor OCR

1. **DPI Alto**: Escanear com 300 DPI ou mais
2. **Contraste**: Ajustar contraste/brilho antes do OCR
3. **Deskew**: Corrigir páginas tortas (`--deskew` no ocrmypdf)
4. **Limpar**: Remover manchas/ruído (`--clean` no ocrmypdf)
5. **Idioma Correto**: Sempre especificar português (`por` ou `pt-BR`)

---

## 🚀 Integração Futura

Em breve podemos adicionar suporte nativo a OCR no projeto:

```python
# Futuro comando automático
python main.py extract documento.pdf --ocr  # Detecta e aplica OCR se necessário
```

Por enquanto, use o workflow acima! 📄✨
