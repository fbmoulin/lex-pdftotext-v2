#!/usr/bin/env python3
"""PDF Legal Text Extractor - CLI.

Extract and structure text from Brazilian legal PDF documents (PJe format).
"""

import shutil
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from tqdm import tqdm

from src.extractors import PyMuPDFExtractor, TableExtractor
from src.formatters import JSONFormatter, MarkdownFormatter, TableFormatter
from src.processors import MetadataParser, TextNormalizer
from src.utils.cache import get_performance_monitor
from src.utils.config import get_config
from src.utils.constants import FILENAME_DISPLAY_LENGTH, MAX_DETAILED_ITEMS, MAX_SUMMARY_ITEMS
from src.utils.exceptions import InvalidPathError
from src.utils.logger import get_logger, setup_logger
from src.utils.validators import (
    check_disk_space,
    estimate_output_size,
    sanitize_output_path,
)

# Load configuration
config = get_config()

# Initialize logging from configuration
setup_logger(log_level=config.log_level, log_file=config.log_file)
logger = get_logger(__name__)


def extract_and_normalize_pdf(pdf_path: Path, normalize: bool = True) -> tuple[str, str, object]:
    """Extract and normalize text from a PDF file.

    Args:
        pdf_path: Path to PDF file
        normalize: Whether to normalize the text

    Returns:
        Tuple of (raw_text, processed_text, metadata)
    """
    # Extract text
    with PyMuPDFExtractor(pdf_path) as extractor:
        raw_text = extractor.extract_text()

    # Normalize if enabled
    if normalize:
        normalizer = TextNormalizer()
        processed_text = normalizer.normalize(raw_text)
        processed_text = normalizer.remove_page_markers(processed_text)
    else:
        processed_text = raw_text

    # Extract metadata
    metadata_parser = MetadataParser()
    doc_metadata = metadata_parser.parse(processed_text)

    return raw_text, processed_text, doc_metadata


def format_output_text(
    processed_text: str,
    doc_metadata: object,
    format: str = "markdown",
    include_metadata: bool = True,
    structured: bool = False,
) -> str:
    """Format processed text for output.

    Args:
        processed_text: Normalized text
        doc_metadata: Extracted metadata
        format: Output format ('markdown', 'txt', or 'json')
        include_metadata: Whether to include metadata header
        structured: Whether to use structured sections (markdown only)

    Returns:
        Formatted output text
    """
    if format == "markdown":
        formatter = MarkdownFormatter()

        if structured:
            return formatter.format_with_sections(processed_text, doc_metadata)
        else:
            return formatter.format(
                processed_text, doc_metadata, include_metadata_header=include_metadata
            )
    elif format == "json":
        # JSON output
        formatter = JSONFormatter()
        return formatter.format_to_string(
            processed_text,
            doc_metadata,
            include_metadata=include_metadata,
            hierarchical=structured,
            indent=2,
        )
    else:
        # Plain text output
        if include_metadata:
            metadata_parser = MetadataParser()
            metadata_str = metadata_parser.format_metadata_as_markdown(doc_metadata)
            return f"{metadata_str}\n\n---\n\n{processed_text}"
        else:
            return processed_text


def safe_move_file(src: Path, dest: Path, create_backup: bool = False) -> bool:
    """Safely move a file with error handling.

    Args:
        src: Source file path
        dest: Destination file path
        create_backup: Whether to backup if destination exists

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create destination directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Handle existing destination
        if dest.exists():
            if create_backup:
                backup_path = dest.with_suffix(dest.suffix + ".bak")
                logger.warning(f"Destination exists, creating backup: {backup_path}")
                shutil.copy2(str(dest), str(backup_path))
            else:
                logger.warning(f"Destination exists, will overwrite: {dest}")

        # Perform move
        shutil.move(str(src), str(dest))
        logger.info(f"File moved successfully: {src} -> {dest}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied moving file {src}: {e}")
        click.echo(f"⚠️  Aviso: Sem permissão para mover arquivo: {src}", err=True)
        return False

    except shutil.Error as e:
        logger.error(f"Error moving file {src}: {e}")
        click.echo(f"⚠️  Aviso: Erro ao mover arquivo: {src}", err=True)
        return False

    except Exception as e:
        logger.error(f"Unexpected error moving file {src}: {e}", exc_info=True)
        click.echo(f"⚠️  Aviso: Erro inesperado ao mover arquivo: {src}", err=True)
        return False


@click.group()
@click.version_option(version="0.3.0")
def cli():
    """PDF Legal Text Extractor.

    Extract and structure text from Brazilian legal PDF documents (PJe format).
    """
    # Load environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path (default: same name as PDF with .md extension)",
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "txt", "json"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--normalize/--no-normalize",
    default=True,
    help="Normalize text (convert UPPERCASE, clean noise) (default: True)",
)
@click.option(
    "--metadata/--no-metadata", default=True, help="Include metadata header (default: True)"
)
@click.option(
    "--structured/--no-structured",
    default=False,
    help="Auto-detect and structure sections (default: False)",
)
def extract(pdf_path, output, format, normalize, metadata, structured):
    """Extract text from a single PDF file.

    Example:
        python main.py extract documento.pdf -o output.md
    """
    pdf_path = Path(pdf_path)

    # Determine output path
    if output is None:
        if format == "markdown":
            output = pdf_path.with_suffix(".md")
        elif format == "json":
            output = pdf_path.with_suffix(".json")
        else:
            output = pdf_path.with_suffix(".txt")
    else:
        # Validate and sanitize user-provided output path
        output = Path(output)
        try:
            output = sanitize_output_path(output, pdf_path.parent)
        except InvalidPathError as e:
            click.echo(f"❌ Erro: Caminho de saída inválido: {e}", err=True)
            sys.exit(1)

    click.echo(f"📄 Extraindo texto de: {pdf_path.name}")

    try:
        # Get page count before extraction
        with PyMuPDFExtractor(pdf_path) as extractor:
            click.echo(f"   Páginas: {extractor.get_page_count()}")

        # Extract and normalize text
        if normalize:
            click.echo("   Normalizando texto...")
        raw_text, processed_text, doc_metadata = extract_and_normalize_pdf(pdf_path, normalize)

        # Format output
        click.echo(f"   Formatando como {format.title()}...")
        output_text = format_output_text(
            processed_text,
            doc_metadata,
            format=format,
            include_metadata=metadata,
            structured=structured,
        )

        # Save to file
        click.echo(f"   Salvando em: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        MarkdownFormatter.save_to_file(output_text, str(output))

        click.echo(f"✅ Concluído! Arquivo salvo em: {output}")

        # Show extracted metadata summary
        if doc_metadata.process_number:
            click.echo(f"\n📋 Processo: {doc_metadata.process_number}")
        if doc_metadata.document_ids:
            click.echo(
                f"   IDs: {', '.join(doc_metadata.document_ids[:MAX_SUMMARY_ITEMS])}"
                + (
                    f" (+{len(doc_metadata.document_ids) - MAX_SUMMARY_ITEMS} mais)"
                    if len(doc_metadata.document_ids) > MAX_SUMMARY_ITEMS
                    else ""
                )
            )

        # Move processed PDF to 'processado' folder
        processado_dir = pdf_path.parent / "processado"
        new_pdf_path = processado_dir / pdf_path.name

        if safe_move_file(pdf_path, new_pdf_path):
            click.echo(f"\n📦 PDF movido para: {new_pdf_path}")
        else:
            click.echo(f"\n⚠️  PDF não foi movido (ainda em: {pdf_path})")

    except Exception as e:
        click.echo(f"❌ Erro: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "-o", "--output-dir", type=click.Path(), help="Output directory (default: input_dir/output)"
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "txt", "json"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option("--normalize/--no-normalize", default=True, help="Normalize text (default: True)")
@click.option(
    "--metadata/--no-metadata", default=True, help="Include metadata header (default: True)"
)
def batch(input_dir, output_dir, format, normalize, metadata):
    """Extract text from all PDFs in a directory.

    Example:
        python main.py batch ./data/input -o ./data/output
    """
    input_dir = Path(input_dir)

    # Determine output directory
    if output_dir is None:
        output_dir = input_dir / "output"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDFs
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        click.echo(f"❌ Nenhum arquivo PDF encontrado em: {input_dir}")
        sys.exit(1)

    click.echo(f"📁 Encontrados {len(pdf_files)} arquivos PDF")
    click.echo(f"📂 Salvando em: {output_dir}\n")

    # Check disk space
    try:
        total_estimated_mb = sum(estimate_output_size(pdf) for pdf in pdf_files)
        required_mb = max(total_estimated_mb, config.min_disk_space_mb)

        has_space, available_mb = check_disk_space(output_dir, required_mb)

        if not has_space:
            click.echo(
                f"⚠️  Aviso: Espaço em disco insuficiente!\n"
                f"   Disponível: {available_mb}MB\n"
                f"   Estimado: {total_estimated_mb}MB\n"
                f"   Recomendado: {required_mb}MB",
                err=True,
            )

            if not click.confirm("Deseja continuar mesmo assim?"):
                click.echo("❌ Operação cancelada pelo usuário")
                sys.exit(1)
        else:
            logger.info(
                f"Disk space check passed: {available_mb}MB available, "
                f"{total_estimated_mb}MB estimated for {len(pdf_files)} files"
            )
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        click.echo(f"⚠️  Aviso: Não foi possível verificar espaço em disco: {e}", err=True)

    # Process each PDF
    success_count = 0
    error_count = 0

    with tqdm(pdf_files, desc="Processando PDFs", unit="arquivo") as pbar:
        for pdf_path in pbar:
            pbar.set_description(f"Processando {pdf_path.name[:FILENAME_DISPLAY_LENGTH]}")

            try:
                # Determine output path
                if format == "markdown":
                    output_path = output_dir / pdf_path.with_suffix(".md").name
                elif format == "json":
                    output_path = output_dir / pdf_path.with_suffix(".json").name
                else:
                    output_path = output_dir / pdf_path.with_suffix(".txt").name

                # Extract and normalize text
                raw_text, processed_text, doc_metadata = extract_and_normalize_pdf(
                    pdf_path, normalize
                )

                # Format output
                output_text = format_output_text(
                    processed_text, doc_metadata, format=format, include_metadata=metadata
                )

                # Save to file
                MarkdownFormatter.save_to_file(output_text, str(output_path))

                # Move processed PDF to 'processado' folder
                processado_dir = input_dir / "processado"
                new_pdf_path = processado_dir / pdf_path.name

                if not safe_move_file(pdf_path, new_pdf_path):
                    tqdm.write(f"⚠️  {pdf_path.name}: Arquivo processado mas não movido")

                success_count += 1

            except Exception as e:
                error_count += 1
                tqdm.write(f"❌ Erro em {pdf_path.name}: {str(e)}")

    # Summary
    click.echo("\n✅ Concluído!")
    click.echo(f"   Sucesso: {success_count} arquivos")
    if error_count > 0:
        click.echo(f"   Erros: {error_count} arquivos")


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "-o", "--output", type=click.Path(), help="Output file path (auto-generated if not specified)"
)
@click.option("--normalize/--no-normalize", default=True, help="Normalize text (default: True)")
@click.option(
    "--format",
    type=click.Choice(["markdown", "txt", "json"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--process-number", type=str, help="Merge only PDFs from this specific process number"
)
def merge(input_dir, output, normalize, format, process_number):
    """Merge multiple PDFs of the SAME PROCESS into a single output file.

    Groups PDFs by process number and creates one merged file per process.
    Only PDFs with the same process number are merged together.

    Example:
        python main.py merge ./data/input
        python main.py merge ./data/input --process-number 5015904-66.2025.8.08.0012
    """
    input_dir = Path(input_dir)

    # Find all PDFs recursively (including subdirectories)
    pdf_files = sorted(input_dir.rglob("*.pdf"))

    # Exclude PDFs already in 'processado' folder
    pdf_files = [f for f in pdf_files if "processado" not in f.parts]

    if not pdf_files:
        click.echo(f"❌ Nenhum arquivo PDF encontrado em: {input_dir}")
        sys.exit(1)

    click.echo(f"📁 Encontrados {len(pdf_files)} arquivos PDF (incluindo subpastas)")
    click.echo("🔍 Agrupando por número de processo...\n")

    # Group PDFs by process number
    metadata_parser = MetadataParser()
    process_groups = {}  # {process_number: [(pdf_path, text, metadata), ...]}

    # First pass: extract and group by process number
    for pdf_path in pdf_files:
        try:
            # Extract and normalize text
            raw_text, processed_text, doc_metadata = extract_and_normalize_pdf(pdf_path, normalize)

            # Get process number
            proc_num = doc_metadata.process_number
            if not proc_num:
                # Try to extract from filename
                import re

                match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", pdf_path.name)
                proc_num = match.group(0) if match else "UNKNOWN"

            # Group by process number
            if proc_num not in process_groups:
                process_groups[proc_num] = []

            process_groups[proc_num].append((pdf_path, processed_text, doc_metadata))

        except Exception as e:
            click.echo(f"   ⚠️  Erro ao processar {pdf_path.name}: {str(e)}")
            continue

    # Show grouping results
    click.echo(f"📊 Encontrados {len(process_groups)} processo(s) diferente(s):\n")
    for proc_num, files in process_groups.items():
        click.echo(f"   • Processo {proc_num}: {len(files)} arquivo(s)")

    # Filter by process number if specified
    if process_number:
        if process_number in process_groups:
            process_groups = {process_number: process_groups[process_number]}
            click.echo(f"\n🎯 Mesclando apenas processo: {process_number}")
        else:
            click.echo(f"\n❌ Processo {process_number} não encontrado!")
            sys.exit(1)

    click.echo()

    # Process each group
    files_created = []
    for proc_num, files in process_groups.items():
        if len(files) == 1 and not process_number:
            click.echo(f"⏭️  Processo {proc_num}: apenas 1 arquivo, pulando merge...")
            continue

        # Determine output filename
        if output:
            # Validate user-provided output path
            output_path = Path(output)
            try:
                output_path = sanitize_output_path(output_path, input_dir)
            except InvalidPathError as e:
                click.echo(f"❌ Erro: Caminho de saída inválido: {e}", err=True)
                sys.exit(1)
        else:
            # Auto-generate filename
            safe_proc = proc_num.replace("/", "-")
            output_path = input_dir / f"processo_{safe_proc}_merged.md"

        click.echo(f"📝 Mesclando {len(files)} arquivo(s) do processo {proc_num}...")

        # Build merged content
        combined_sections = []

        for i, (pdf_path, text, metadata) in enumerate(files, 1):
            section_parts = []

            # Document separator
            section_parts.append(f"## Documento {i}: {pdf_path.name}")

            # Metadata
            if format == "markdown":
                metadata_md = metadata_parser.format_metadata_as_markdown(metadata)
                if metadata_md:
                    section_parts.append("\n**Metadados:**\n")
                    section_parts.append(metadata_md)

            # Content
            section_parts.append("\n### Conteúdo\n")
            section_parts.append(text)

            combined_sections.append("\n".join(section_parts))

        # Build final document
        if format == "markdown":
            final_content = f"# Processo {proc_num} - Consolidado\n\n"
            final_content += f"*Mesclado a partir de {len(files)} arquivo(s) PDF*\n\n"
            final_content += "---\n\n"
            final_content += "\n\n---\n\n".join(combined_sections)
        else:
            final_content = f"PROCESSO {proc_num} - CONSOLIDADO\n\n"
            final_content += f"Mesclado a partir de {len(files)} arquivo(s) PDF\n\n"
            final_content += "=" * 80 + "\n\n"
            final_content += ("\n\n" + "=" * 80 + "\n\n").join(combined_sections)

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        MarkdownFormatter.save_to_file(final_content, str(output_path))

        click.echo(f"   ✅ Salvo em: {output_path}")
        files_created.append(output_path)

        # Move processed PDFs to 'processado' folder
        processado_dir = input_dir / "processado"
        moved_count = 0

        for pdf_path, _, _ in files:
            # Preserve subdirectory structure
            relative_path = pdf_path.relative_to(input_dir)
            new_pdf_path = processado_dir / relative_path

            if safe_move_file(pdf_path, new_pdf_path):
                moved_count += 1

        if moved_count > 0:
            click.echo(f"   📦 {moved_count} PDF(s) movido(s) para: {processado_dir}")
        if moved_count < len(files):
            click.echo(f"   ⚠️  {len(files) - moved_count} PDF(s) não foram movidos")

    # Summary
    click.echo(f"\n🎉 Concluído! {len(files_created)} arquivo(s) mesclado(s) criado(s)")
    for f in files_created:
        click.echo(f"   📄 {f}")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def info(pdf_path):
    """Show metadata information about a PDF without extracting full text.

    Example:
        python main.py info documento.pdf
    """
    pdf_path = Path(pdf_path)

    click.echo(f"📄 Analisando: {pdf_path.name}\n")

    try:
        # Extract text
        with PyMuPDFExtractor(pdf_path) as extractor:
            pdf_metadata = extractor.get_metadata()
            raw_text = extractor.extract_text()

        # Parse legal metadata
        metadata_parser = MetadataParser()
        doc_metadata = metadata_parser.parse(raw_text)

        # Display PDF metadata
        click.echo("📋 Metadados do PDF:")
        if pdf_metadata["title"]:
            click.echo(f"   Título: {pdf_metadata['title']}")
        if pdf_metadata["author"]:
            click.echo(f"   Autor: {pdf_metadata['author']}")
        click.echo(f"   Páginas: {pdf_metadata['page_count']}")
        if pdf_metadata["creation_date"]:
            click.echo(f"   Criado em: {pdf_metadata['creation_date']}")

        # Display legal metadata
        click.echo("\n⚖️  Metadados Jurídicos:")
        if doc_metadata.process_number:
            click.echo(f"   Processo: {doc_metadata.process_number}")
        if doc_metadata.court:
            click.echo(f"   Vara: {doc_metadata.court}")
        if doc_metadata.case_value:
            click.echo(f"   Valor: R$ {doc_metadata.case_value}")
        if doc_metadata.author:
            click.echo(f"   Autor: {doc_metadata.author}")
        if doc_metadata.defendant:
            click.echo(f"   Réu: {doc_metadata.defendant}")

        if doc_metadata.document_ids:
            click.echo(f"\n   IDs dos Documentos ({len(doc_metadata.document_ids)}):")
            for doc_id in doc_metadata.document_ids[:MAX_DETAILED_ITEMS]:
                click.echo(f"      - {doc_id}")
            if len(doc_metadata.document_ids) > MAX_DETAILED_ITEMS:
                click.echo(
                    f"      ... e mais {len(doc_metadata.document_ids) - MAX_DETAILED_ITEMS}"
                )

        if doc_metadata.lawyers:
            click.echo(f"\n   Advogados ({len(doc_metadata.lawyers)}):")
            for lawyer in doc_metadata.lawyers:
                click.echo(f"      - {lawyer['name']} (OAB/{lawyer['state']} {lawyer['oab']})")

        if doc_metadata.signature_dates:
            click.echo(
                f"\n   Assinaturas: {', '.join(doc_metadata.signature_dates[:MAX_SUMMARY_ITEMS])}"
            )

        # Document type
        doc_types = []
        if doc_metadata.is_initial_petition:
            doc_types.append("Petição Inicial")
        if doc_metadata.is_decision:
            doc_types.append("Decisão/Despacho")
        if doc_metadata.is_certificate:
            doc_types.append("Certidão")

        if doc_types:
            click.echo(f"\n   Tipo: {', '.join(doc_types)}")

    except Exception as e:
        click.echo(f"❌ Erro: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--reset", is_flag=True, help="Reset performance metrics after displaying report")
@click.option("--json", "output_json", is_flag=True, help="Output metrics as JSON")
def perf_report(reset, output_json):
    """Show performance metrics report.

    Displays timing statistics for PDF processing operations.

    Example:
        python main.py perf-report
        python main.py perf-report --reset
        python main.py perf-report --json
    """
    import json as json_module

    performance = get_performance_monitor()
    metrics = performance.get_metrics()

    if not metrics:
        click.echo("📊 No performance metrics collected yet.")
        click.echo("\n💡 Tip: Run some PDF extraction commands first to collect metrics.")
        return

    if output_json:
        # Output as JSON
        click.echo(json_module.dumps(metrics, indent=2))
    else:
        # Output as formatted report
        click.echo("\n" + performance.report())

    if reset:
        performance.reset()
        click.echo("\n✅ Performance metrics have been reset.")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path (default: same name as PDF with _tables.md extension)",
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "csv"], case_sensitive=False),
    default="markdown",
    help="Output format: markdown tables or separate CSV files (default: markdown)",
)
@click.option(
    "--include-metadata/--no-metadata",
    default=True,
    help="Include table metadata (page number, position) (default: True)",
)
def extract_tables(pdf_path, output, format, include_metadata):
    """Extract tables from a PDF file.

    Detects and extracts all tables from the PDF, outputting them as
    Markdown tables or CSV files.

    Example:
        python main.py extract-tables documento.pdf
        python main.py extract-tables documento.pdf --format csv -o tables_dir/
    """
    pdf_path = Path(pdf_path)

    click.echo(f"📊 Extraindo tabelas de: {pdf_path.name}")

    try:
        # Extract tables
        extractor = TableExtractor(pdf_path)
        click.echo("   Detectando tabelas...")
        tables = extractor.extract_tables()

        if not tables:
            click.echo("ℹ️  Nenhuma tabela encontrada no documento.")
            return

        click.echo(f"   Encontradas {len(tables)} tabela(s)")

        # Output based on format
        if format == "csv":
            # Determine output directory
            if output is None:
                output_dir = pdf_path.parent / f"{pdf_path.stem}_tables"
            else:
                output_dir = Path(output)

            click.echo(f"   Salvando CSVs em: {output_dir}")
            csv_files = extractor.extract_tables_as_csv(output_dir)

            click.echo(f"\n✅ Concluído! {len(csv_files)} arquivos CSV criados:")
            for csv_file in csv_files:
                click.echo(f"   - {csv_file.name}")

        else:  # markdown
            # Determine output path
            if output is None:
                output = pdf_path.with_name(f"{pdf_path.stem}_tables.md")
            else:
                output = Path(output)

            # Format tables as Markdown
            click.echo("   Formatando como Markdown...")
            formatter = TableFormatter()
            markdown_output = formatter.format_all_tables(tables, include_metadata=include_metadata)

            # Add header
            header = f"# Tabelas Extraídas - {pdf_path.name}\n\n"
            header += f"**Total de tabelas:** {len(tables)}\n\n"
            header += "---\n\n"
            markdown_output = header + markdown_output

            # Save to file
            click.echo(f"   Salvando em: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            MarkdownFormatter.save_to_file(markdown_output, str(output))

            click.echo(f"\n✅ Concluído! Tabelas salvas em: {output}")

        # Display summary
        click.echo("\n📋 Resumo:")
        for i, table in enumerate(tables[:5], 1):  # Show first 5 tables
            click.echo(
                f"   Tabela {i}: Página {table['page'] + 1} - "
                f"{table['rows']} linhas × {table['cols']} colunas"
            )
        if len(tables) > 5:
            click.echo(f"   ... e mais {len(tables) - 5} tabela(s)")

    except Exception as e:
        click.echo(f"❌ Erro: {str(e)}", err=True)
        logger.error(f"Error extracting tables from {pdf_path}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
