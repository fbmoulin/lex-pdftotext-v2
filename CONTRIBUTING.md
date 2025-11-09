# Contribuindo para PDF Legal Extractor

> **Projeto da [Lex Intelligentia](https://lexintelligentia.com)** - Desenvolvido por Felipe Moulin

Obrigado por considerar contribuir para o PDF Legal Extractor! 🎉

## 🤝 Como Contribuir

### Reportar Bugs

Se encontrou um bug, por favor abra uma [issue](https://github.com/fbmoulin/pdftotext/issues) com:

- **Descrição clara** do problema
- **Passos para reproduzir** o bug
- **Comportamento esperado** vs **comportamento atual**
- **Screenshots** (se aplicável)
- **Informações do sistema**:
  - OS: Windows/Linux/macOS
  - Python version: `python --version`
  - Versão do app: `git describe --tags`

### Sugerir Melhorias

Abra uma [issue](https://github.com/fbmoulin/pdftotext/issues) com tag `enhancement`:

- Descreva a funcionalidade desejada
- Explique por que seria útil
- Sugira possível implementação (opcional)

### Pull Requests

1. **Fork** o repositório

1. **Clone** seu fork:

   ```bash
   git clone https://github.com/SEU_USUARIO/pdftotext.git
   ```

1. **Crie uma branch** para sua feature:

   ```bash
   git checkout -b feature/minha-feature
   ```

1. **Faça suas alterações** seguindo o guia de estilo

1. **Execute os testes**:

   ```bash
   pytest tests/
   ```

1. **Commit** suas mudanças:

   ```bash
   git commit -m "feat: Adiciona nova funcionalidade"
   ```

1. **Push** para seu fork:

   ```bash
   git push origin feature/minha-feature
   ```

1. **Abra um Pull Request** no repositório original

## 📝 Guia de Estilo

### Código Python

- Siga [PEP 8](https://pep8.org/)
- Use **type hints** quando possível
- Docstrings em inglês no código, comentários em português OK
- Máximo 100 caracteres por linha

```python
def extract_pdf(pdf_path: Path, options: dict) -> str:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file
        options: Extraction options

    Returns:
        Extracted text as string

    Raises:
        PDFExtractionError: If extraction fails
    """
    pass
```

### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update dependencies
```

### Testes

- Adicione testes para novas funcionalidades
- Mantenha cobertura > 80%
- Execute `pytest` antes de fazer PR

## 🛠️ Setup de Desenvolvimento

```bash
# Clone
git clone https://github.com/SEU_USUARIO/pdftotext.git
cd pdftotext

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

# Instalar em modo desenvolvimento
pip install -r requirements.txt
pip install -e .

# Instalar ferramentas de dev (opcional)
pip install black flake8 mypy pytest-cov

# Rodar testes
pytest tests/ -v

# Rodar com cobertura
pytest --cov=src tests/
```

## 📚 Estrutura do Código

```
src/
├── extractors/     # Extração de PDF
├── processors/     # Processamento de texto
├── formatters/     # Formatação de saída
└── utils/          # Utilidades
```

## 🎯 Áreas que Precisam de Ajuda

- [ ] Suporte a mais formatos de documentos jurídicos
- [ ] Melhorias na detecção de metadados
- [ ] Testes unitários adicionais
- [ ] Documentação de exemplos
- [ ] Tradução para inglês
- [ ] Performance optimization
- [ ] Suporte a OCR nativo (integrado)
- [ ] API REST opcional

## ❓ Dúvidas?

Abra uma [discussão](https://github.com/fbmoulin/pdftotext/discussions) ou issue!

## 📄 Licença

Este projeto é licenciado sob a **MIT License**. Ao contribuir, você concorda que suas contribuições
serão licenciadas sob a mesma licença MIT.

Veja o arquivo [LICENSE](./LICENSE) para detalhes completos.
