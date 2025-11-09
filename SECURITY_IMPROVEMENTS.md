# Melhorias de Segurança e Estabilidade

Baseado nas melhores práticas do **Docling** (IBM Research) e padrões da indústria para aplicações
Python de processamento de documentos.

## 🔒 Segurança

### 1. Validação de Entrada com Pydantic

**Prática do Docling**: Usa Pydantic v2 para validação de dados em runtime.

**Implementação Sugerida**:

```python
from pydantic import BaseModel, Field, validator
from pathlib import Path
from typing import Optional


class PDFInputConfig(BaseModel):
    """Validação de entrada para PDFs."""

    pdf_path: Path
    max_file_size_mb: int = Field(default=500, ge=1, le=1000)
    allowed_extensions: list[str] = [".pdf"]

    @validator("pdf_path")
    def validate_pdf_path(cls, v):
        if not v.exists():
            raise ValueError(f"Arquivo não encontrado: {v}")
        if not v.is_file():
            raise ValueError(f"Caminho não é um arquivo: {v}")
        if v.suffix.lower() not in cls.allowed_extensions:
            raise ValueError(f"Extensão inválida: {v.suffix}")

        # Verificar tamanho do arquivo
        size_mb = v.stat().st_size / (1024 * 1024)
        if size_mb > cls.max_file_size_mb:
            raise ValueError(f"Arquivo muito grande: {size_mb:.2f}MB")

        return v


class DocumentMetadataValidated(BaseModel):
    """Metadados validados."""

    process_number: Optional[str] = Field(
        None, regex=r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"
    )
    author: Optional[str] = Field(None, max_length=500)
    defendant: Optional[str] = Field(None, max_length=500)
    document_ids: list[str] = Field(default_factory=list)
```

### 2. Sanitização de Caminhos

**Problema**: Path traversal attacks (`../../etc/passwd`)

```python
from pathlib import Path


def sanitize_output_path(user_input: str, base_dir: Path) -> Path:
    """Sanitiza caminho de saída para prevenir path traversal."""
    # Resolver caminho absoluto
    output_path = (base_dir / user_input).resolve()

    # Verificar se está dentro do diretório permitido
    if not str(output_path).startswith(str(base_dir.resolve())):
        raise ValueError(f"Caminho inválido: tentativa de path traversal")

    return output_path
```

### 3. Limite de Recursos

**Prática do Docling**: Execução local para ambientes air-gapped.

```python
import resource
import signal
from contextlib import contextmanager


@contextmanager
def resource_limit(max_memory_mb=1024, max_time_seconds=300):
    """Limita recursos durante processamento."""

    def timeout_handler(signum, frame):
        raise TimeoutError("Processamento excedeu tempo limite")

    # Configurar timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(max_time_seconds)

    # Limitar memória (apenas Unix)
    try:
        max_memory_bytes = max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
    except (ValueError, OSError):
        pass  # Windows não suporta

    try:
        yield
    finally:
        signal.alarm(0)  # Cancelar timeout
```

### 4. Logging de Segurança

```python
import logging
import hashlib
from pathlib import Path

# Configurar logger de auditoria
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler("audit.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
audit_logger.addHandler(handler)


def audit_file_access(pdf_path: Path, user: str = "system"):
    """Registra acesso a arquivos para auditoria."""
    # Hash do arquivo para integridade
    file_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    audit_logger.info(
        f"FILE_ACCESS | user={user} | path={pdf_path} | "
        f"size={pdf_path.stat().st_size} | sha256={file_hash[:16]}..."
    )
```

## 🛡️ Estabilidade

### 1. Retry com Exponential Backoff

```python
import time
from functools import wraps
from typing import Callable, Type


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator para retry com exponential backoff."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_factor**attempt
                        time.sleep(wait_time)
                        continue
                    raise

            raise last_exception

        return wrapper

    return decorator


# Uso
@retry(max_attempts=3, exceptions=(IOError, OSError))
def extract_pdf_with_retry(pdf_path):
    with PyMuPDFExtractor(pdf_path) as extractor:
        return extractor.extract_text()
```

### 2. Circuit Breaker Pattern

```python
from datetime import datetime, timedelta
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"  # Normal
    OPEN = "open"  # Falhas detectadas
    HALF_OPEN = "half_open"  # Testando recuperação


class CircuitBreaker:
    """Previne cascata de falhas."""

    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker está aberto")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### 3. Validação de PDF Corrupto

```python
import fitz  # PyMuPDF


def validate_pdf_integrity(pdf_path: Path) -> tuple[bool, str]:
    """Valida integridade do PDF antes de processar."""
    try:
        doc = fitz.open(pdf_path)

        # Verificações básicas
        if doc.page_count == 0:
            return False, "PDF vazio (0 páginas)"

        if doc.is_encrypted:
            return False, "PDF criptografado (não suportado)"

        # Testar primeira página
        try:
            first_page = doc[0]
            _ = first_page.get_text()
        except Exception as e:
            return False, f"Erro ao ler primeira página: {e}"

        doc.close()
        return True, "OK"

    except fitz.FileDataError:
        return False, "Arquivo PDF corrompido"
    except Exception as e:
        return False, f"Erro desconhecido: {e}"
```

### 4. Tratamento de Erros Robusto

```python
class PDFExtractionError(Exception):
    """Erro base para extração de PDF."""

    pass


class PDFCorruptedError(PDFExtractionError):
    """PDF corrompido ou ilegível."""

    pass


class PDFEncryptedError(PDFExtractionError):
    """PDF criptografado."""

    pass


class PDFTooLargeError(PDFExtractionError):
    """PDF excede tamanho máximo."""

    pass


# Uso no extractor
class PyMuPDFExtractorSecure(PyMuPDFExtractor):
    """Versão com validações de segurança."""

    def __init__(self, pdf_path: Path, max_size_mb: int = 500):
        # Validar entrada
        config = PDFInputConfig(pdf_path=pdf_path, max_file_size_mb=max_size_mb)

        # Validar integridade
        valid, message = validate_pdf_integrity(config.pdf_path)
        if not valid:
            raise PDFCorruptedError(f"PDF inválido: {message}")

        # Log de auditoria
        audit_file_access(config.pdf_path)

        super().__init__(config.pdf_path)
```

## 📊 Monitoramento

### 1. Métricas de Performance

```python
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractionMetrics:
    """Métricas de extração."""

    pdf_path: str
    page_count: int
    file_size_mb: float
    extraction_time_seconds: float
    text_length: int
    success: bool
    error: Optional[str] = None

    def to_dict(self):
        return {
            "pdf_path": self.pdf_path,
            "page_count": self.page_count,
            "file_size_mb": self.file_size_mb,
            "extraction_time_seconds": self.extraction_time_seconds,
            "text_length": self.text_length,
            "success": self.success,
            "error": self.error,
        }


def extract_with_metrics(pdf_path: Path) -> tuple[str, ExtractionMetrics]:
    """Extrai texto e coleta métricas."""
    start_time = time.time()
    error = None
    text = ""
    page_count = 0

    try:
        with PyMuPDFExtractor(pdf_path) as extractor:
            page_count = extractor.get_page_count()
            text = extractor.extract_text()
        success = True
    except Exception as e:
        success = False
        error = str(e)
    finally:
        elapsed = time.time() - start_time

        metrics = ExtractionMetrics(
            pdf_path=str(pdf_path),
            page_count=page_count,
            file_size_mb=pdf_path.stat().st_size / (1024 * 1024),
            extraction_time_seconds=elapsed,
            text_length=len(text),
            success=success,
            error=error,
        )

    return text, metrics
```

### 2. Health Check

```python
import psutil
from pathlib import Path


def health_check() -> dict:
    """Verifica saúde do sistema."""
    return {
        "status": "healthy",
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "temp_dir_writable": Path("/tmp").is_dir() and os.access("/tmp", os.W_OK),
    }
```

## 📝 Checklist de Implementação

### Fase 1 - Crítico (Semana 1)

- [ ] Adicionar Pydantic para validação de entrada
- [ ] Implementar sanitização de caminhos
- [ ] Validar integridade de PDFs antes de processar
- [ ] Adicionar logging de auditoria
- [ ] Tratar PDFs criptografados/corrompidos

### Fase 2 - Importante (Semana 2)

- [ ] Implementar limite de tamanho de arquivo
- [ ] Adicionar timeout para processamento
- [ ] Retry com exponential backoff
- [ ] Métricas de performance
- [ ] Testes de segurança (fuzzing básico)

### Fase 3 - Desejável (Semana 3)

- [ ] Circuit breaker para batch processing
- [ ] Health check endpoint (se API)
- [ ] Rate limiting (se API)
- [ ] Monitoramento de recursos
- [ ] Documentação de segurança

## 🔧 Dependências Adicionais

```txt
# Adicionar ao requirements.txt
pydantic>=2.0.0          # Validação de dados
psutil>=5.9.0            # Monitoramento de recursos
python-magic>=0.4.27     # Detecção de tipo de arquivo
```

## 📚 Referências

- [Docling GitHub](https://github.com/docling-project/docling) - Práticas da IBM Research
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Vulnerabilidades comuns
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Pydantic Documentation](https://docs.pydantic.dev/) - Validação de dados
