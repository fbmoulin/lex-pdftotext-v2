#!/usr/bin/env python3
"""PDF Legal Text Extractor - GUI Application.

Interface gráfica para extração de texto de PDFs judiciais brasileiros.
"""

import os
import shutil
import sys
from pathlib import Path

import webview
from dotenv import load_dotenv

from src.extractors import PyMuPDFExtractor
from src.formatters import MarkdownFormatter
from src.processors import (
    ImageAnalyzer,
    MetadataParser,
    TextNormalizer,
    format_image_description_markdown,
)
from src.utils.config import get_config
from src.utils.exceptions import PDFExtractionError
from src.utils.logger import get_logger, setup_logger


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller.

    Args:
        relative_path: Relative path from the application root

    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent

    return base_path / relative_path


# Load configuration
config = get_config()

# Initialize logging from configuration
setup_logger(log_level=config.log_level, log_file=config.log_file)
logger = get_logger(__name__)


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
        return False

    except shutil.Error as e:
        logger.error(f"Error moving file {src}: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error moving file {src}: {e}", exc_info=True)
        return False


class API:
    """Backend API for PyWebview interface."""

    def __init__(self):
        """Initialize the API with default state."""
        self.window = None
        self.last_output_path = None  # Store last generated file path

    def select_folder(self):
        """Open folder selection dialog.

        Returns:
            str: Selected folder path
        """
        try:
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG, allow_multiple=False)
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception:
            return None

    def select_file(self):
        """Open file selection dialog.

        Returns:
            str: Selected file path
        """
        try:
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG, file_types=("PDF Files (*.pdf)",), allow_multiple=False
            )
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception:
            return None

    def open_folder(self, file_path=None):
        """Open folder containing the file in system file explorer.

        Args:
            file_path: Path to file (optional, uses last_output_path if not provided)

        Returns:
            dict: Success status
        """
        try:
            import platform
            import subprocess

            # Use provided path or last output path
            if file_path is None:
                if not self.last_output_path:
                    raise Exception("Nenhum arquivo foi gerado ainda")
                file_path = self.last_output_path

            folder_path = Path(file_path).parent

            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])

            return {"success": True, "message": f"Pasta aberta: {folder_path}"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao abrir pasta: {str(e)}"}

    def save_as(self):
        """Open save dialog to export file to another location.

        Returns:
            str: Selected save path or None
        """
        try:
            if not self.last_output_path or not Path(self.last_output_path).exists():
                raise Exception("Nenhum arquivo foi gerado ainda")

            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=Path(self.last_output_path).name,
                file_types=("Markdown Files (*.md)",),
            )

            if result:
                # Copy file to new location
                import shutil

                shutil.copy2(self.last_output_path, result)
                return {"success": True, "path": result, "message": f"Arquivo salvo em: {result}"}

            return {"success": False, "message": "Operação cancelada"}
        except Exception as e:
            return {"success": False, "message": f"Erro: {str(e)}"}

    def extract_pdf(self, pdf_path, options):
        """Extract text from a single PDF.

        Args:
            pdf_path: Path to PDF file
            options: Dictionary with options (normalize, metadata, structured, analyze_images)

        Returns:
            dict: Success status and message
        """
        try:
            pdf_path = Path(pdf_path)

            # Generate output path
            output_path = pdf_path.with_suffix(".md")

            # Extract text and images
            with PyMuPDFExtractor(pdf_path) as extractor:
                raw_text = extractor.extract_text()

                # Extract images if option is enabled
                images = []
                if options.get("analyze_images", False):
                    images = extractor.extract_images()

            # Process text
            if options.get("normalize", True):
                normalizer = TextNormalizer()
                processed_text = normalizer.normalize(raw_text)
                processed_text = normalizer.remove_page_markers(processed_text)
            else:
                processed_text = raw_text

            # Extract metadata
            metadata_parser = MetadataParser()
            doc_metadata = metadata_parser.parse(processed_text)

            # Analyze images if any were found and option is enabled
            image_descriptions = ""
            if images and options.get("analyze_images", False):
                try:
                    analyzer = ImageAnalyzer()
                    analyzed_images = analyzer.describe_images_batch(
                        images, context="documento judicial brasileiro"
                    )

                    # Format image descriptions
                    image_descriptions = "\n\n## 📸 Imagens Anexadas\n\n"
                    for idx, img_data in enumerate(analyzed_images, 1):
                        image_descriptions += format_image_description_markdown(img_data, idx)

                except ValueError:
                    # API key not configured - skip image analysis
                    image_descriptions = f"\n\n## ⚠️ Imagens Detectadas\n\n{len(images)} imagem(ns) encontrada(s), mas análise não foi possível (configure GEMINI_API_KEY).\n\n"
                except Exception as e:
                    # Other error - log but continue
                    image_descriptions = f"\n\n## ⚠️ Erro na Análise de Imagens\n\n{str(e)}\n\n"

            # Format output
            formatter = MarkdownFormatter()

            if options.get("structured", False):
                output_text = formatter.format_with_sections(processed_text, doc_metadata)
            else:
                output_text = formatter.format(
                    processed_text,
                    doc_metadata,
                    include_metadata_header=options.get("metadata", True),
                )

            # Append image descriptions
            output_text += image_descriptions

            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            MarkdownFormatter.save_to_file(output_text, str(output_path))

            # Store last output path for export functions
            self.last_output_path = str(output_path)

            # Move to processed
            processado_dir = pdf_path.parent / "processado"
            new_pdf_path = processado_dir / pdf_path.name

            # Build success message
            if safe_move_file(pdf_path, new_pdf_path):
                message = f"✅ Sucesso! Arquivo salvo em: {output_path}\n📦 PDF movido para: {new_pdf_path}"
            else:
                message = f"✅ Sucesso! Arquivo salvo em: {output_path}\n⚠️ PDF não foi movido (ainda em: {pdf_path})"
            if images:
                message += f"\n🖼️ {len(images)} imagem(ns) processada(s)"

            return {
                "success": True,
                "output_path": str(output_path),
                "pdf_moved": str(new_pdf_path),
                "message": message,
            }

        except PDFExtractionError as e:
            return {"success": False, "message": f"❌ Erro ao processar PDF: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"❌ Erro inesperado: {str(e)}"}

    def batch_process(self, input_dir, options):
        """Process all PDFs in a directory.

        Args:
            input_dir: Input directory path
            options: Dictionary with options (normalize, metadata, output_dir)

        Returns:
            str: Success message
        """
        try:
            input_dir = Path(input_dir)

            # Determine output directory
            output_dir = options.get("output_dir")
            if output_dir:
                output_dir = Path(output_dir)
            else:
                output_dir = input_dir / "output"

            output_dir.mkdir(parents=True, exist_ok=True)

            # Find all PDFs
            pdf_files = list(input_dir.glob("*.pdf"))

            if not pdf_files:
                raise Exception(f"Nenhum arquivo PDF encontrado em: {input_dir}")

            # Process each PDF
            success_count = 0
            error_count = 0
            errors = []

            for pdf_path in pdf_files:
                try:
                    # Extract text
                    with PyMuPDFExtractor(pdf_path) as extractor:
                        raw_text = extractor.extract_text()

                    # Process text
                    if options.get("normalize", True):
                        normalizer = TextNormalizer()
                        processed_text = normalizer.normalize(raw_text)
                        processed_text = normalizer.remove_page_markers(processed_text)
                    else:
                        processed_text = raw_text

                    # Extract metadata
                    metadata_parser = MetadataParser()
                    doc_metadata = metadata_parser.parse(processed_text)

                    # Format output
                    formatter = MarkdownFormatter()
                    output_text = formatter.format(
                        processed_text,
                        doc_metadata,
                        include_metadata_header=options.get("metadata", True),
                    )

                    # Save to file
                    output_path = output_dir / pdf_path.with_suffix(".md").name
                    MarkdownFormatter.save_to_file(output_text, str(output_path))

                    # Move processed PDF
                    processado_dir = input_dir / "processado"
                    new_pdf_path = processado_dir / pdf_path.name

                    if not safe_move_file(pdf_path, new_pdf_path):
                        logger.warning(f"Could not move {pdf_path.name}, but extraction succeeded")

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"{pdf_path.name}: {str(e)}")

            # Summary
            message = "✅ Concluído!\n"
            message += f"   Sucesso: {success_count} arquivo(s)\n"
            if error_count > 0:
                message += f"   Erros: {error_count} arquivo(s)\n"
                message += "\nDetalhes dos erros:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    message += f"\n... e mais {len(errors) - 5} erro(s)"

            return message

        except Exception as e:
            raise Exception(f"Erro no processamento em lote: {str(e)}") from e

    def merge_process(self, input_dir, options):
        """Merge multiple PDFs of the same process.

        Args:
            input_dir: Input directory path
            options: Dictionary with options (normalize, process_number)

        Returns:
            str: Success message
        """
        try:
            input_dir = Path(input_dir)
            import re

            # Find all PDFs recursively
            pdf_files = sorted(input_dir.rglob("*.pdf"))

            # Exclude PDFs in processado folder
            pdf_files = [f for f in pdf_files if "processado" not in f.parts]

            if not pdf_files:
                raise Exception(f"Nenhum arquivo PDF encontrado em: {input_dir}")

            # Group PDFs by process number
            metadata_parser = MetadataParser()
            normalizer = TextNormalizer() if options.get("normalize", True) else None
            process_groups = {}

            for pdf_path in pdf_files:
                try:
                    # Extract text
                    with PyMuPDFExtractor(pdf_path) as extractor:
                        raw_text = extractor.extract_text()

                    # Normalize if enabled
                    if normalizer:
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
                        match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", pdf_path.name)
                        proc_num = match.group(0) if match else "UNKNOWN"

                    # Group by process number
                    if proc_num not in process_groups:
                        process_groups[proc_num] = []

                    process_groups[proc_num].append((pdf_path, processed_text, doc_metadata))

                except Exception:
                    continue

            # Filter by process number if specified
            process_number = options.get("process_number")
            if process_number:
                if process_number in process_groups:
                    process_groups = {process_number: process_groups[process_number]}
                else:
                    raise Exception(f"Processo {process_number} não encontrado!")

            # Process each group
            files_created = []
            for proc_num, files in process_groups.items():
                if len(files) == 1 and not process_number:
                    continue  # Skip single-file processes

                # Build merged content
                combined_sections = []

                for i, (pdf_path, text, metadata) in enumerate(files, 1):
                    section_parts = []

                    # Document separator
                    section_parts.append(f"## Documento {i}: {pdf_path.name}")

                    # Metadata
                    metadata_md = metadata_parser.format_metadata_as_markdown(metadata)
                    if metadata_md:
                        section_parts.append("\n**Metadados:**\n")
                        section_parts.append(metadata_md)

                    # Content
                    section_parts.append("\n### Conteúdo\n")
                    section_parts.append(text)

                    combined_sections.append("\n".join(section_parts))

                # Build final document
                safe_proc = proc_num.replace("/", "-")
                output_path = input_dir / f"processo_{safe_proc}_merged.md"

                final_content = f"# Processo {proc_num} - Consolidado\n\n"
                final_content += f"*Mesclado a partir de {len(files)} arquivo(s) PDF*\n\n"
                final_content += "---\n\n"
                final_content += "\n\n---\n\n".join(combined_sections)

                # Save
                output_path.parent.mkdir(parents=True, exist_ok=True)
                MarkdownFormatter.save_to_file(final_content, str(output_path))

                files_created.append((proc_num, len(files), output_path))

                # Move processed PDFs
                processado_dir = input_dir / "processado"

                for pdf_path, _, _ in files:
                    relative_path = pdf_path.relative_to(input_dir)
                    new_pdf_path = processado_dir / relative_path
                    safe_move_file(pdf_path, new_pdf_path)

            # Summary
            if not files_created:
                return "ℹ️ Nenhum processo com múltiplos volumes encontrado."

            message = f"✅ Concluído! {len(files_created)} processo(s) mesclado(s):\n\n"
            for proc_num, file_count, output_path in files_created:
                message += f"• Processo {proc_num}: {file_count} arquivo(s)\n"
                message += f"  📄 {output_path.name}\n"

            return message

        except Exception as e:
            raise Exception(f"Erro ao mesclar processos: {str(e)}") from e


def main():
    """Main application entry point."""
    # Load environment variables from .env file
    env_path = get_resource_path(".env")
    load_dotenv(env_path)

    # Create API instance
    api = API()

    # Get HTML path using PyInstaller-aware path resolution
    html_path = get_resource_path("assets/html/index.html")

    if not html_path.exists():
        print(f"❌ Erro: Arquivo HTML não encontrado: {html_path}")
        print(f"   Diretório base: {get_resource_path('')}")
        print("   Conteúdo do diretório:")
        try:
            for item in get_resource_path("").iterdir():
                print(f"     - {item.name}")
        except Exception as e:
            print(f"   Erro ao listar: {e}")
        sys.exit(1)

    # Create window
    window = webview.create_window(
        "PDF Legal Extractor",
        html_path.as_uri(),
        js_api=api,
        width=900,
        height=750,
        resizable=True,
        min_size=(800, 600),
    )

    # Store window reference in API
    api.window = window

    # Start application
    webview.start(debug=False)


if __name__ == "__main__":
    main()
