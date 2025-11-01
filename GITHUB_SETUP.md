# Como Criar Repositório no GitHub - Guia Passo a Passo

## 📋 Passo 1: Criar Repositório no GitHub

1. Acesse https://github.com
2. Faça login na sua conta
3. Clique no botão **"+"** no canto superior direito
4. Selecione **"New repository"**

### Configurações do Repositório

- **Repository name**: `pdftotext` ou `pdf-legal-extractor`
- **Description**: `Extração inteligente de texto de documentos judiciais brasileiros (PJe) - Interface GUI e CLI`
- **Visibility**:
  - ✅ **Public** (recomendado) - Compartilhar com comunidade
  - ou **Private** - Apenas você tem acesso
- **Initialize repository**:
  - ❌ **NÃO** marque "Add a README file"
  - ❌ **NÃO** marque "Add .gitignore"
  - ❌ **NÃO** marque "Choose a license"

  (Já temos esses arquivos localmente)

5. Clique em **"Create repository"**

### Copie a URL do Repositório

Após criar, você verá a URL, algo como:
```
https://github.com/fbmoulin/pdftotext.git
```

**COPIE ESSA URL!** Vamos usá-la nos próximos passos.

---

## 📋 Passo 2: Configurar Git Localmente (Se Necessário)

```bash
# Configure seu nome e email (apenas uma vez por máquina)
git config --global user.name "Felipe Moulin"
git config --global user.email "seu-email@example.com"

# Verificar configuração
git config --global user.name
git config --global user.email
```

---

## 📋 Passo 3: Inicializar e Fazer Commit Inicial

Os comandos abaixo já estão prontos. Copie e execute:

```bash
# Inicializar repositório Git
git init

# Adicionar todos os arquivos (respeitando .gitignore)
git add .

# Ver o que será commitado
git status

# Fazer commit inicial
git commit -m "Initial commit: PDF Legal Extractor with GUI

- Complete CLI with extract, batch, and merge commands
- Modern PyWebview GUI interface
- PDF validation and security features
- Automated build system with PyInstaller
- Inno Setup installer script
- Comprehensive documentation
- MIT License"

# Renomear branch para 'main' (padrão do GitHub)
git branch -M main

# Conectar ao repositório remoto (SUBSTITUA A URL PELA SUA!)
git remote add origin https://github.com/fbmoulin/pdftotext.git

# Verificar remote
git remote -v

# Fazer push inicial
git push -u origin main
```

**IMPORTANTE**: Substitua `https://github.com/fbmoulin/pdftotext.git` pela URL que você copiou no Passo 1!

---

## 📋 Passo 4: Autenticação

### Opção 1: Personal Access Token (Recomendado)

Se aparecer pedindo senha, **NÃO use sua senha do GitHub** (não funciona mais).

1. Acesse https://github.com/settings/tokens
2. Clique em **"Generate new token"** → **"Generate new token (classic)"**
3. Dê um nome: `pdftotext-repo`
4. Marque os escopos: `repo` (todos)
5. Clique em **"Generate token"**
6. **COPIE O TOKEN** (só aparece uma vez!)
7. Quando pedir senha no terminal, **cole o token**

### Opção 2: SSH (Alternativa)

```bash
# Gerar chave SSH (se não tiver)
ssh-keygen -t ed25519 -C "seu-email@example.com"

# Copiar chave pública
cat ~/.ssh/id_ed25519.pub

# Adicionar no GitHub:
# https://github.com/settings/keys → New SSH key
```

Depois, use URL SSH ao invés de HTTPS:
```bash
git remote set-url origin git@github.com:fbmoulin/pdftotext.git
```

---

## 📋 Passo 5: Verificar no GitHub

1. Acesse `https://github.com/seu-usuario/pdftotext`
2. Você deve ver todos os arquivos
3. O README.md será exibido automaticamente na página principal

---

## 🏷️ Passo 6: Criar Tags de Versão (Opcional)

```bash
# Criar tag da versão inicial
git tag -a v1.0.0 -m "Release v1.0.0: First stable release

Features:
- CLI with extract, batch, and merge commands
- Modern PyWebview GUI
- PDF validation and security
- Automated build and installer
- Comprehensive documentation"

# Enviar tag para GitHub
git push origin v1.0.0

# Ou enviar todas as tags
git push --tags
```

---

## 📝 Comandos Futuros (Após Mudanças)

```bash
# Ver status
git status

# Adicionar arquivos modificados
git add .

# Commit com mensagem
git commit -m "feat: Add new feature description"

# Enviar para GitHub
git push
```

### Convenção de Commits (Recomendado)

```bash
git commit -m "feat: Nova funcionalidade"
git commit -m "fix: Correção de bug"
git commit -m "docs: Atualização de documentação"
git commit -m "refactor: Refatoração de código"
git commit -m "test: Adição de testes"
git commit -m "chore: Tarefas de manutenção"
```

---

## 🎨 Adicionar Badge ao README (Opcional)

Adicione ao topo do README.md:

```markdown
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
```

---

## 🔧 Troubleshooting

### Erro: "remote origin already exists"

```bash
# Remover remote existente
git remote remove origin

# Adicionar novamente
git remote add origin https://github.com/seu-usuario/pdftotext.git
```

### Erro: "Authentication failed"

- Use Personal Access Token ao invés da senha
- Ou configure SSH

### Erro: "rejected - non-fast-forward"

```bash
# Forçar push (cuidado, sobrescreve remote!)
git push -f origin main

# Ou fazer pull primeiro
git pull origin main --rebase
git push origin main
```

---

## 📊 Depois de Publicar

### Melhorar README

Adicione screenshots, GIFs, exemplos visuais.

### GitHub Pages

Se quiser hospedar documentação:
```bash
# Settings → Pages → Source: main branch / docs folder
```

### GitHub Actions

Criar workflow de CI/CD para testes automáticos:
`.github/workflows/test.yml`

### Issues e Discussions

Habilite:
- Settings → Features → ✅ Issues
- Settings → Features → ✅ Discussions

---

## 📚 Recursos Adicionais

- [GitHub Docs](https://docs.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Pronto!** Seu projeto estará no GitHub e disponível para a comunidade. 🎉
