#!/usr/bin/env python3
"""
PDF Legal Text Extractor - CLI

Extract and structure text from Brazilian legal PDF documents (PJe format).
"""

import sys
from pathlib import Path
import shutil
import click
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors import PyMuPDFExtractor
from src.processors import TextNormalizer, MetadataParser
from src.formatters import MarkdownFormatter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    PDF Legal Text Extractor

    Extract and structure text from Brazilian legal PDF documents (PJe format).
    """
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output file path (default: same name as PDF with .md extension)'
)
@click.option(
    '--format',
    type=click.Choice(['markdown', 'txt'], case_sensitive=False),
    default='markdown',
    help='Output format (default: markdown)'
)
@click.option(
    '--normalize/--no-normalize',
    default=True,
    help='Normalize text (convert UPPERCASE, clean noise) (default: True)'
)
@click.option(
    '--metadata/--no-metadata',
    default=True,
    help='Include metadata header (default: True)'
)
@click.option(
    '--structured/--no-structured',
    default=False,
    help='Auto-detect and structure sections (default: False)'
)
def extract(pdf_path, output, format, normalize, metadata, structured):
    """
    Extract text from a single PDF file.

    Example:
        python main.py extract documento.pdf -o output.md
    """
    pdf_path = Path(pdf_path)

    # Determine output path
    if output is None:
        if format == 'markdown':
            output = pdf_path.with_suffix('.md')
        else:
            output = pdf_path.with_suffix('.txt')
    else:
        output = Path(output)

    click.echo(f"📄 Extraindo texto de: {pdf_path.name}")

    try:
        # Extract text
        with PyMuPDFExtractor(pdf_path) as extractor:
            click.echo(f"   Páginas: {extractor.get_page_count()}")
            raw_text = extractor.extract_text()

        # Process text
        if normalize:
            click.echo("   Normalizando texto...")
            normalizer = TextNormalizer()
            processed_text = normalizer.normalize(raw_text)
            processed_text = normalizer.remove_page_markers(processed_text)
        else:
            processed_text = raw_text

        # Extract metadata
        click.echo("   Extraindo metadados...")
        metadata_parser = MetadataParser()
        doc_metadata = metadata_parser.parse(processed_text)

        # Format output
        if format == 'markdown':
            click.echo("   Formatando como Markdown...")
            formatter = MarkdownFormatter()

            if structured:
                output_text = formatter.format_with_sections(
                    processed_text,
                    doc_metadata
                )
            else:
                output_text = formatter.format(
                    processed_text,
                    doc_metadata,
                    include_metadata_header=metadata
                )
        else:
            # Plain text output
            if metadata:
                metadata_str = metadata_parser.format_metadata_as_markdown(doc_metadata)
                output_text = f"{metadata_str}\n\n---\n\n{processed_text}"
            else:
                output_text = processed_text

        # Save to file
        click.echo(f"   Salvando em: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        MarkdownFormatter.save_to_file(output_text, str(output))

        click.echo(f"✅ Concluído! Arquivo salvo em: {output}")

        # Show extracted metadata summary
        if doc_metadata.process_number:
            click.echo(f"\n📋 Processo: {doc_metadata.process_number}")
        if doc_metadata.document_ids:
            click.echo(f"   IDs: {', '.join(doc_metadata.document_ids[:3])}" +
                      (f" (+{len(doc_metadata.document_ids)-3} mais)" if len(doc_metadata.document_ids) > 3 else ""))

        # Move processed PDF to 'processado' folder
        processado_dir = pdf_path.parent / 'processado'
        processado_dir.mkdir(parents=True, exist_ok=True)
        new_pdf_path = processado_dir / pdf_path.name
        shutil.move(str(pdf_path), str(new_pdf_path))
        click.echo(f"\n📦 PDF movido para: {new_pdf_path}")

    except Exception as e:
        click.echo(f"❌ Erro: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.option(
    '-o', '--output-dir',
    type=click.Path(),
    help='Output directory (default: input_dir/output)'
)
@click.option(
    '--format',
    type=click.Choice(['markdown', 'txt'], case_sensitive=False),
    default='markdown',
    help='Output format (default: markdown)'
)
@click.option(
    '--normalize/--no-normalize',
    default=True,
    help='Normalize text (default: True)'
)
@click.option(
    '--metadata/--no-metadata',
    default=True,
    help='Include metadata header (default: True)'
)
def batch(input_dir, output_dir, format, normalize, metadata):
    """
    Extract text from all PDFs in a directory.

    Example:
        python main.py batch ./data/input -o ./data/output
    """
    input_dir = Path(input_dir)

    # Determine output directory
    if output_dir is None:
        output_dir = input_dir / 'output'
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDFs
    pdf_files = list(input_dir.glob('*.pdf'))

    if not pdf_files:
        click.echo(f"❌ Nenhum arquivo PDF encontrado em: {input_dir}")
        sys.exit(1)

    click.echo(f"📁 Encontrados {len(pdf_files)} arquivos PDF")
    click.echo(f"📂 Salvando em: {output_dir}\n")

    # Process each PDF
    success_count = 0
    error_count = 0

    with tqdm(pdf_files, desc="Processando PDFs", unit="arquivo") as pbar:
        for pdf_path in pbar:
            pbar.set_description(f"Processando {pdf_path.name[:30]}")

            try:
                # Determine output path
                if format == 'markdown':
                    output_path = output_dir / pdf_path.with_suffix('.md').name
                else:
                    output_path = output_dir / pdf_path.with_suffix('.txt').name

                # Extract text
                with PyMuPDFExtractor(pdf_path) as extractor:
                    raw_text = extractor.extract_text()

                # Process text
                if normalize:
                    normalizer = TextNormalizer()
                    processed_text = normalizer.normalize(raw_text)
                    processed_text = normalizer.remove_page_markers(processed_text)
                else:
                    processed_text = raw_text

                # Extract metadata
                metadata_parser = MetadataParser()
                doc_metadata = metadata_parser.parse(processed_text)

                # Format output
                if format == 'markdown':
                    formatter = MarkdownFormatter()
                    output_text = formatter.format(
                        processed_text,
                        doc_metadata,
                        include_metadata_header=metadata
                    )
                else:
                    if metadata:
                        metadata_str = metadata_parser.format_metadata_as_markdown(doc_metadata)
                        output_text = f"{metadata_str}\n\n---\n\n{processed_text}"
                    else:
                        output_text = processed_text

                # Save to file
                MarkdownFormatter.save_to_file(output_text, str(output_path))

                # Move processed PDF to 'processado' folder
                processado_dir = input_dir / 'processado'
                processado_dir.mkdir(parents=True, exist_ok=True)
                new_pdf_path = processado_dir / pdf_path.name
                shutil.move(str(pdf_path), str(new_pdf_path))

                success_count += 1

            except Exception as e:
                error_count += 1
                tqdm.write(f"❌ Erro em {pdf_path.name}: {str(e)}")

    # Summary
    click.echo(f"\n✅ Concluído!")
    click.echo(f"   Sucesso: {success_count} arquivos")
    if error_count > 0:
        click.echo(f"   Erros: {error_count} arquivos")


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output file path (auto-generated if not specified)'
)
@click.option(
    '--normalize/--no-normalize',
    default=True,
    help='Normalize text (default: True)'
)
@click.option(
    '--format',
    type=click.Choice(['markdown', 'txt'], case_sensitive=False),
    default='markdown',
    help='Output format (default: markdown)'
)
@click.option(
    '--process-number',
    type=str,
    help='Merge only PDFs from this specific process number'
)
def merge(input_dir, output, normalize, format, process_number):
    """
    Merge multiple PDFs of the SAME PROCESS into a single output file.

    Groups PDFs by process number and creates one merged file per process.
    Only PDFs with the same process number are merged together.

    Example:
        python main.py merge ./data/input
        python main.py merge ./data/input --process-number 5015904-66.2025.8.08.0012
    """
    input_dir = Path(input_dir)

    # Find all PDFs recursively (including subdirectories)
    pdf_files = sorted(list(input_dir.rglob('*.pdf')))

    # Exclude PDFs already in 'processado' folder
    pdf_files = [f for f in pdf_files if 'processado' not in f.parts]

    if not pdf_files:
        click.echo(f"❌ Nenhum arquivo PDF encontrado em: {input_dir}")
        sys.exit(1)

    click.echo(f"📁 Encontrados {len(pdf_files)} arquivos PDF (incluindo subpastas)")
    click.echo(f"🔍 Agrupando por número de processo...\n")

    # Group PDFs by process number
    metadata_parser = MetadataParser()
    normalizer = TextNormalizer() if normalize else None
    process_groups = {}  # {process_number: [(pdf_path, text, metadata), ...]}

    # First pass: extract and group by process number
    for pdf_path in pdf_files:
        try:
            # Quick extraction to get process number
            with PyMuPDFExtractor(pdf_path) as extractor:
                raw_text = extractor.extract_text()

            # Normalize if enabled
            if normalize:
                processed_text = normalizer.normalize(raw_text)
                processed_text = normalizer.remove_page_markers(processed_text)
            else:
                processed_text = raw_text

            # Extract metadata
            doc_metadata = metadata_parser.parse(processed_text)

            # Get process number
            proc_num = doc_metadata.process_number
            if not proc_num:
                # Try to extract from filename
                import re
                match = re.search(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}', pdf_path.name)
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
            output_path = Path(output)
        else:
            # Auto-generate filename
            safe_proc = proc_num.replace('/', '-')
            output_path = input_dir / f"processo_{safe_proc}_merged.md"

        click.echo(f"📝 Mesclando {len(files)} arquivo(s) do processo {proc_num}...")

        # Build merged content
        combined_sections = []

        for i, (pdf_path, text, metadata) in enumerate(files, 1):
            section_parts = []

            # Document separator
            section_parts.append(f"## Documento {i}: {pdf_path.name}")

            # Metadata
            if format == 'markdown':
                metadata_md = metadata_parser.format_metadata_as_markdown(metadata)
                if metadata_md:
                    section_parts.append("\n**Metadados:**\n")
                    section_parts.append(metadata_md)

            # Content
            section_parts.append("\n### Conteúdo\n")
            section_parts.append(text)

            combined_sections.append('\n'.join(section_parts))

        # Build final document
        if format == 'markdown':
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
        processado_dir = input_dir / 'processado'
        processado_dir.mkdir(parents=True, exist_ok=True)

        for pdf_path, _, _ in files:
            # Preserve subdirectory structure
            relative_path = pdf_path.relative_to(input_dir)
            new_pdf_path = processado_dir / relative_path
            new_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(pdf_path), str(new_pdf_path))

        click.echo(f"   📦 {len(files)} PDF(s) movido(s) para: {processado_dir}")

    # Summary
    click.echo(f"\n🎉 Concluído! {len(files_created)} arquivo(s) mesclado(s) criado(s)")
    for f in files_created:
        click.echo(f"   📄 {f}")


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
def info(pdf_path):
    """
    Show metadata information about a PDF without extracting full text.

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
        if pdf_metadata['title']:
            click.echo(f"   Título: {pdf_metadata['title']}")
        if pdf_metadata['author']:
            click.echo(f"   Autor: {pdf_metadata['author']}")
        click.echo(f"   Páginas: {pdf_metadata['page_count']}")
        if pdf_metadata['creation_date']:
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
            for doc_id in doc_metadata.document_ids[:5]:
                click.echo(f"      - {doc_id}")
            if len(doc_metadata.document_ids) > 5:
                click.echo(f"      ... e mais {len(doc_metadata.document_ids) - 5}")

        if doc_metadata.lawyers:
            click.echo(f"\n   Advogados ({len(doc_metadata.lawyers)}):")
            for lawyer in doc_metadata.lawyers:
                click.echo(f"      - {lawyer['name']} (OAB/{lawyer['state']} {lawyer['oab']})")

        if doc_metadata.signature_dates:
            click.echo(f"\n   Assinaturas: {', '.join(doc_metadata.signature_dates[:3])}")

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


if __name__ == '__main__':
    cli()
