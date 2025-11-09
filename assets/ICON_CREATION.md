# Criação de Ícone para o Aplicativo

## Ícone Necessário

Para o empacotamento do aplicativo, precisamos de um ícone no formato `.ico` com múltiplas
resoluções.

### Especificações Recomendadas

- **Formato**: `.ico` (Windows Icon)
- **Resoluções**: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- **Cores**: 32-bit (com canal alfa para transparência)

## Opções para Criar o Ícone

### 1. Ferramenta Online (Mais Fácil)

**ICO Convert** - https://icoconvert.com/

1. Faça upload de uma imagem PNG de alta qualidade (512x512 ou maior)
1. Selecione "Custom sizes"
1. Marque: 16, 32, 48, 64, 128, 256
1. Clique em "Convert ICO"
1. Baixe o arquivo `logo.ico`

**Favicon.io** - https://favicon.io/

- Converte emoji ou texto em ícone
- Suporta geração automática de múltiplas resoluções

### 2. GIMP (Gratuito)

1. Abra GIMP
1. Crie ou abra uma imagem quadrada (512x512)
1. **Arquivo → Exportar Como**
1. Salve como `logo.ico`
1. Na caixa de diálogo, selecione múltiplas resoluções
1. Clique em "Exportar"

### 3. Photoshop / Illustrator

1. Crie design em 512x512
1. Use plugin ICO para exportar:
   - Photoshop: ICO (Windows Icon) Format Plugin
   - Illustrator: Export for Screens → ICO

### 4. Inkscape (Vetor, Gratuito)

1. Crie design vetorial
1. **Arquivo → Exportar PNG**
1. Exporte como 512x512
1. Use ferramenta online para converter PNG → ICO

## Design Sugerido para PDF Extractor

### Conceito 1: Documento com Engrenagem

- Símbolo de documento (📄) + engrenagem (⚙️)
- Cores: Azul (#667eea) e Roxo (#764ba2) - gradiente do app
- Representa automação de extração de PDFs

### Conceito 2: PDF → MD

- Seta transformando PDF em MD
- Minimalista e direto
- Cores corporativas

### Conceito 3: Documento Jurídico

- Balança da justiça (⚖️) + documento
- Representa contexto jurídico/legal
- Cores sóbrias (azul escuro, dourado)

## Paleta de Cores do App

```
Primário: #667eea (Azul-roxo)
Secundário: #764ba2 (Roxo)
Gradiente: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
Texto: #2d3748 (Cinza escuro)
Fundo: #f7fafc (Cinza claro)
```

## Atalho Rápido com Emoji (Temporário)

Se precisar de um ícone rapidamente para testes:

1. Acesse https://emoji-favicon.vercel.app/
1. Escolha emoji 📄 ou ⚖️
1. Baixe como `.ico`
1. Renomeie para `logo.ico`

## Localização do Ícone

Após criar, salve em:

```
/assets/logo.ico
```

## Verificação do Ícone

Verifique se o ícone tem múltiplas resoluções:

**Windows**:

```powershell
Get-ItemProperty assets\logo.ico | Select-Object *
```

**Linux**:

```bash
identify assets/logo.ico
```

Deve mostrar algo como:

```
logo.ico[0] ICO 256x256
logo.ico[1] ICO 128x128
logo.ico[2] ICO 64x64
logo.ico[3] ICO 48x48
logo.ico[4] ICO 32x32
logo.ico[5] ICO 16x16
```

## Próximo Passo

Após criar o ícone, coloque-o em `/assets/logo.ico` e prossiga com o build:

```bash
python build_exe.py
```

O ícone será automaticamente incorporado no executável pelo PyInstaller.
