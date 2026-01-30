#!/usr/bin/env python3
"""lex-pdftotext CLI.

Extract and structure text from Brazilian legal PDF documents (PJe format).
"""

import shutil
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from tqdm import tqdm

from . import __version__
from .extractors import PyMuPDFExtractor, TableExtractor
from .formatters import JSONFormatter, MarkdownFormatter, TableFormatter
from .processors import DocumentMetadata, MetadataParser, TextNormalizer
from .utils.cache import get_performance_monitor
from .utils.config import get_config
from .utils.constants import FILENAME_DISPLAY_LENGTH, MAX_DETAILED_ITEMS, MAX_SUMMARY_ITEMS
from .utils.exceptions import InvalidPathError
from .utils.logger import get_logger, setup_logger
from .utils.validators import (
    check_disk_space,
    estimate_output_size,
    sanitize_output_path,
)

# Load configuration
config = get_config()

# Initialize logging from configuration
setup_logger(log_level=config.log_level, log_file=config.log_file)
logger = get_logger(__name__)


def extract_and_normalize_pdf(
    pdf_path: Path, normalize: bool = True
) -> tuple[str, str, DocumentMetadata]:
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
    doc_metadata: DocumentMetadata,
    format: str = "markdown",
    include_metadata: bool = True,
    structured: bool = False,
    indexed: bool = False,
) -> str:
    """Format processed text for output.

    Args:
        processed_text: Normalized text
        doc_metadata: Extracted metadata
        format: Output format ('markdown', 'txt', or 'json')
        include_metadata: Whether to include metadata header
        structured: Whether to use structured sections (markdown only)
        indexed: Whether to generate index with anchors (markdown only)

    Returns:
        Formatted output text
    """
    if format == "markdown":
        md_formatter = MarkdownFormatter()

        if indexed:
            return md_formatter.format_with_index(
                processed_text, doc_metadata, include_metadata_header=include_metadata
            )
        elif structured:
            return md_formatter.format_with_sections(processed_text, doc_metadata)
        else:
            return md_formatter.format(
                processed_text, doc_metadata, include_metadata_header=include_metadata
            )
    elif format == "json":
        # JSON output
        json_formatter = JSONFormatter()
        return json_formatter.format_to_string(
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
        click.echo(f"Warning: No permission to move file: {src}", err=True)
        return False

    except shutil.Error as e:
        logger.error(f"Error moving file {src}: {e}")
        click.echo(f"Warning: Error moving file: {src}", err=True)
        return False

    except Exception as e:
        logger.error(f"Unexpected error moving file {src}: {e}", exc_info=True)
        click.echo(f"Warning: Unexpected error moving file: {src}", err=True)
        return False


@click.group()
@click.version_option(version=__version__)
def cli():
    """lex-pdftotext: PDF Legal Text Extractor.

    Extract and structure text from Brazilian legal PDF documents (PJe format).
    """
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
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
@click.option(
    "--indexed/--no-indexed",
    default=False,
    help="Generate index with document anchors and cross-references (default: False)",
)
def extract(pdf_path, output, format, normalize, metadata, structured, indexed):
    """Extract text from a single PDF file.

    Example:
        lex-pdftotext extract documento.pdf -o output.md
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
            click.echo(f"Error: Invalid output path: {e}", err=True)
            sys.exit(1)

    click.echo(f"Extracting text from: {pdf_path.name}")

    try:
        # Get page count before extraction
        with PyMuPDFExtractor(pdf_path) as extractor:
            click.echo(f"   Pages: {extractor.get_page_count()}")

        # Extract and normalize text
        if normalize:
            click.echo("   Normalizing text...")
        raw_text, processed_text, doc_metadata = extract_and_normalize_pdf(pdf_path, normalize)

        # If indexed mode, extract document positions from raw text
        # (positions are lost during normalization)
        if indexed:
            from .utils.patterns import RegexPatterns

            doc_metadata.document_positions = RegexPatterns.extract_document_ids_with_positions(
                raw_text
            )

        # Format output
        click.echo(f"   Formatting as {format.title()}...")
        output_text = format_output_text(
            processed_text,
            doc_metadata,
            format=format,
            include_metadata=metadata,
            structured=structured,
            indexed=indexed,
        )

        # Save to file
        click.echo(f"   Saving to: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        MarkdownFormatter.save_to_file(output_text, str(output))

        click.echo(f"Done! File saved to: {output}")

        # Show extracted metadata summary
        if doc_metadata.process_number:
            click.echo(f"\nProcess: {doc_metadata.process_number}")
        if doc_metadata.document_ids:
            click.echo(
                f"   IDs: {', '.join(doc_metadata.document_ids[:MAX_SUMMARY_ITEMS])}"
                + (
                    f" (+{len(doc_metadata.document_ids) - MAX_SUMMARY_ITEMS} more)"
                    if len(doc_metadata.document_ids) > MAX_SUMMARY_ITEMS
                    else ""
                )
            )

        # Move processed PDF to 'processado' folder
        processado_dir = pdf_path.parent / "processado"
        new_pdf_path = processado_dir / pdf_path.name

        if safe_move_file(pdf_path, new_pdf_path):
            click.echo(f"\nPDF moved to: {new_pdf_path}")
        else:
            click.echo(f"\nPDF not moved (still at: {pdf_path})")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
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
        lex-pdftotext batch ./data/input -o ./data/output
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
        click.echo(f"No PDF files found in: {input_dir}")
        sys.exit(1)

    click.echo(f"Found {len(pdf_files)} PDF files")
    click.echo(f"Saving to: {output_dir}\n")

    # Check disk space
    try:
        total_estimated_mb = sum(estimate_output_size(pdf) for pdf in pdf_files)
        required_mb = max(total_estimated_mb, config.min_disk_space_mb)

        has_space, available_mb = check_disk_space(output_dir, required_mb)

        if not has_space:
            click.echo(
                f"Warning: Insufficient disk space!\n"
                f"   Available: {available_mb}MB\n"
                f"   Estimated: {total_estimated_mb}MB\n"
                f"   Recommended: {required_mb}MB",
                err=True,
            )

            if not click.confirm("Continue anyway?"):
                click.echo("Operation cancelled by user")
                sys.exit(1)
        else:
            logger.info(
                f"Disk space check passed: {available_mb}MB available, "
                f"{total_estimated_mb}MB estimated for {len(pdf_files)} files"
            )
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        click.echo(f"Warning: Could not check disk space: {e}", err=True)

    # Process each PDF
    success_count = 0
    error_count = 0

    with tqdm(pdf_files, desc="Processing PDFs", unit="file") as pbar:
        for pdf_path in pbar:
            pbar.set_description(f"Processing {pdf_path.name[:FILENAME_DISPLAY_LENGTH]}")

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
                    tqdm.write(f"Warning: {pdf_path.name}: File processed but not moved")

                success_count += 1

            except Exception as e:
                error_count += 1
                tqdm.write(f"Error in {pdf_path.name}: {str(e)}")

    # Summary
    click.echo("\nDone!")
    click.echo(f"   Success: {success_count} files")
    if error_count > 0:
        click.echo(f"   Errors: {error_count} files")


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
        lex-pdftotext merge ./data/input
        lex-pdftotext merge ./data/input --process-number 5015904-66.2025.8.08.0012
    """
    input_dir = Path(input_dir)

    # Find all PDFs recursively (including subdirectories)
    pdf_files = sorted(input_dir.rglob("*.pdf"))

    # Exclude PDFs already in 'processado' folder
    pdf_files = [f for f in pdf_files if "processado" not in f.parts]

    if not pdf_files:
        click.echo(f"No PDF files found in: {input_dir}")
        sys.exit(1)

    click.echo(f"Found {len(pdf_files)} PDF files (including subdirectories)")
    click.echo("Grouping by process number...\n")

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
            click.echo(f"   Warning: Error processing {pdf_path.name}: {str(e)}")
            continue

    # Show grouping results
    click.echo(f"Found {len(process_groups)} different process(es):\n")
    for proc_num, files in process_groups.items():
        click.echo(f"   - Process {proc_num}: {len(files)} file(s)")

    # Filter by process number if specified
    if process_number:
        if process_number in process_groups:
            process_groups = {process_number: process_groups[process_number]}
            click.echo(f"\nMerging only process: {process_number}")
        else:
            click.echo(f"\nProcess {process_number} not found!")
            sys.exit(1)

    click.echo()

    # Process each group
    files_created = []
    for proc_num, files in process_groups.items():
        if len(files) == 1 and not process_number:
            click.echo(f"Skipping process {proc_num}: only 1 file...")
            continue

        # Determine output filename
        if output:
            # Validate user-provided output path
            output_path = Path(output)
            try:
                output_path = sanitize_output_path(output_path, input_dir)
            except InvalidPathError as e:
                click.echo(f"Error: Invalid output path: {e}", err=True)
                sys.exit(1)
        else:
            # Auto-generate filename
            safe_proc = proc_num.replace("/", "-")
            output_path = input_dir / f"processo_{safe_proc}_merged.md"

        click.echo(f"Merging {len(files)} file(s) from process {proc_num}...")

        # Build merged content
        combined_sections = []

        for i, (pdf_path, text, doc_metadata) in enumerate(files, 1):
            section_parts = []

            # Document separator
            section_parts.append(f"## Document {i}: {pdf_path.name}")

            # Metadata
            if format == "markdown":
                metadata_md = metadata_parser.format_metadata_as_markdown(doc_metadata)
                if metadata_md:
                    section_parts.append("\n**Metadata:**\n")
                    section_parts.append(metadata_md)

            # Content
            section_parts.append("\n### Content\n")
            section_parts.append(text)

            combined_sections.append("\n".join(section_parts))

        # Build final document
        if format == "markdown":
            final_content = f"# Process {proc_num} - Consolidated\n\n"
            final_content += f"*Merged from {len(files)} PDF file(s)*\n\n"
            final_content += "---\n\n"
            final_content += "\n\n---\n\n".join(combined_sections)
        else:
            final_content = f"PROCESS {proc_num} - CONSOLIDATED\n\n"
            final_content += f"Merged from {len(files)} PDF file(s)\n\n"
            final_content += "=" * 80 + "\n\n"
            final_content += ("\n\n" + "=" * 80 + "\n\n").join(combined_sections)

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        MarkdownFormatter.save_to_file(final_content, str(output_path))

        click.echo(f"   Saved to: {output_path}")
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
            click.echo(f"   {moved_count} PDF(s) moved to: {processado_dir}")
        if moved_count < len(files):
            click.echo(f"   Warning: {len(files) - moved_count} PDF(s) were not moved")

    # Summary
    click.echo(f"\nDone! {len(files_created)} merged file(s) created")
    for f in files_created:
        click.echo(f"   {f}")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def info(pdf_path):
    """Show metadata information about a PDF without extracting full text.

    Example:
        lex-pdftotext info documento.pdf
    """
    pdf_path = Path(pdf_path)

    click.echo(f"Analyzing: {pdf_path.name}\n")

    try:
        # Extract text
        with PyMuPDFExtractor(pdf_path) as extractor:
            pdf_metadata = extractor.get_metadata()
            raw_text = extractor.extract_text()

        # Parse legal metadata
        metadata_parser = MetadataParser()
        doc_metadata = metadata_parser.parse(raw_text)

        # Display PDF metadata
        click.echo("PDF Metadata:")
        if pdf_metadata["title"]:
            click.echo(f"   Title: {pdf_metadata['title']}")
        if pdf_metadata["author"]:
            click.echo(f"   Author: {pdf_metadata['author']}")
        click.echo(f"   Pages: {pdf_metadata['page_count']}")
        if pdf_metadata["creation_date"]:
            click.echo(f"   Created: {pdf_metadata['creation_date']}")

        # Display legal metadata
        click.echo("\nLegal Metadata:")
        if doc_metadata.process_number:
            click.echo(f"   Process: {doc_metadata.process_number}")
        if doc_metadata.court:
            click.echo(f"   Court: {doc_metadata.court}")
        if doc_metadata.case_value:
            click.echo(f"   Value: R$ {doc_metadata.case_value}")
        if doc_metadata.author:
            click.echo(f"   Author: {doc_metadata.author}")
        if doc_metadata.defendant:
            click.echo(f"   Defendant: {doc_metadata.defendant}")

        if doc_metadata.document_ids:
            click.echo(f"\n   Document IDs ({len(doc_metadata.document_ids)}):")
            for doc_id in doc_metadata.document_ids[:MAX_DETAILED_ITEMS]:
                click.echo(f"      - {doc_id}")
            if len(doc_metadata.document_ids) > MAX_DETAILED_ITEMS:
                click.echo(
                    f"      ... and {len(doc_metadata.document_ids) - MAX_DETAILED_ITEMS} more"
                )

        if doc_metadata.lawyers:
            click.echo(f"\n   Lawyers ({len(doc_metadata.lawyers)}):")
            for lawyer in doc_metadata.lawyers:
                click.echo(f"      - {lawyer['name']} (OAB/{lawyer['state']} {lawyer['oab']})")

        if doc_metadata.signature_dates:
            click.echo(
                f"\n   Signatures: {', '.join(doc_metadata.signature_dates[:MAX_SUMMARY_ITEMS])}"
            )

        # Document type
        doc_types = []
        if doc_metadata.is_initial_petition:
            doc_types.append("Initial Petition")
        if doc_metadata.is_decision:
            doc_types.append("Decision/Order")
        if doc_metadata.is_certificate:
            doc_types.append("Certificate")

        if doc_types:
            click.echo(f"\n   Type: {', '.join(doc_types)}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--reset", is_flag=True, help="Reset performance metrics after displaying report")
@click.option("--json", "output_json", is_flag=True, help="Output metrics as JSON")
def perf_report(reset, output_json):
    """Show performance metrics report.

    Displays timing statistics for PDF processing operations.

    Example:
        lex-pdftotext perf-report
        lex-pdftotext perf-report --reset
        lex-pdftotext perf-report --json
    """
    import json as json_module

    performance = get_performance_monitor()
    metrics = performance.get_metrics()

    if not metrics:
        click.echo("No performance metrics collected yet.")
        click.echo("\nTip: Run some PDF extraction commands first to collect metrics.")
        return

    if output_json:
        # Output as JSON
        click.echo(json_module.dumps(metrics, indent=2))
    else:
        # Output as formatted report
        click.echo("\n" + performance.report())

    if reset:
        performance.reset()
        click.echo("\nPerformance metrics have been reset.")


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
        lex-pdftotext extract-tables documento.pdf
        lex-pdftotext extract-tables documento.pdf --format csv -o tables_dir/
    """
    pdf_path = Path(pdf_path)

    click.echo(f"Extracting tables from: {pdf_path.name}")

    try:
        # Extract tables
        extractor = TableExtractor(pdf_path)
        click.echo("   Detecting tables...")
        tables = extractor.extract_tables()

        if not tables:
            click.echo("No tables found in document.")
            return

        click.echo(f"   Found {len(tables)} table(s)")

        # Output based on format
        if format == "csv":
            # Determine output directory
            if output is None:
                output_dir = pdf_path.parent / f"{pdf_path.stem}_tables"
            else:
                output_dir = Path(output)

            click.echo(f"   Saving CSVs to: {output_dir}")
            csv_files = extractor.extract_tables_as_csv(output_dir)

            click.echo(f"\nDone! {len(csv_files)} CSV files created:")
            for csv_file in csv_files:
                click.echo(f"   - {csv_file.name}")

        else:  # markdown
            # Determine output path
            if output is None:
                output = pdf_path.with_name(f"{pdf_path.stem}_tables.md")
            else:
                output = Path(output)

            # Format tables as Markdown
            click.echo("   Formatting as Markdown...")
            formatter = TableFormatter()
            markdown_output = formatter.format_all_tables(tables, include_metadata=include_metadata)

            # Add header
            header = f"# Extracted Tables - {pdf_path.name}\n\n"
            header += f"**Total tables:** {len(tables)}\n\n"
            header += "---\n\n"
            markdown_output = header + markdown_output

            # Save to file
            click.echo(f"   Saving to: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            MarkdownFormatter.save_to_file(markdown_output, str(output))

            click.echo(f"\nDone! Tables saved to: {output}")

        # Display summary
        click.echo("\nSummary:")
        for i, table in enumerate(tables[:5], 1):  # Show first 5 tables
            click.echo(
                f"   Table {i}: Page {table['page'] + 1} - "
                f"{table['rows']} rows x {table['cols']} columns"
            )
        if len(tables) > 5:
            click.echo(f"   ... and {len(tables) - 5} more table(s)")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Error extracting tables from {pdf_path}: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
