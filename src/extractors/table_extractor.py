"""Table extraction from PDF documents using pdfplumber."""

from pathlib import Path

import pdfplumber

from ..utils.cache import get_performance_monitor
from ..utils.exceptions import InvalidPathError
from ..utils.logger import get_logger

# Initialize logger and performance monitor
logger = get_logger(__name__)
performance = get_performance_monitor()


class TableExtractor:
    """
    Extract tables from PDF documents using pdfplumber.

    This extractor is optimized for Brazilian legal documents but works
    with any PDF containing tabular data.
    """

    def __init__(self, pdf_path: str | Path):
        """
        Initialize table extractor.

        Args:
            pdf_path: Path to PDF file

        Raises:
            InvalidPathError: If file doesn't exist or isn't a PDF
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise InvalidPathError(f"Arquivo não encontrado: {pdf_path}")
        if not self.pdf_path.suffix.lower() == ".pdf":
            raise InvalidPathError(f"Arquivo deve ser PDF: {pdf_path}")

    @performance.track("table_extraction")
    def extract_tables(
        self, table_settings: dict | None = None, extract_text: bool = True
    ) -> list[dict]:
        """
        Extract all tables from the PDF.

        Args:
            table_settings: Custom pdfplumber table detection settings
            extract_text: Whether to extract text content from tables

        Returns:
            list[dict]: List of extracted tables, each containing:
                - page: Page number (0-indexed)
                - table_index: Index of table on the page
                - bbox: Bounding box coordinates (x0, y0, x1, y1)
                - data: Table data as list of lists (rows and columns)
                - rows: Number of rows
                - cols: Number of columns

        Example:
            >>> extractor = TableExtractor('document.pdf')
            >>> tables = extractor.extract_tables()
            >>> for table in tables:
            >>>     print(f"Page {table['page']}: {table['rows']}x{table['cols']} table")
        """
        # Default table settings optimized for legal documents
        default_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 1,
            "min_words_horizontal": 1,
        }

        # Merge with custom settings
        settings = {**default_settings, **(table_settings or {})}

        tables = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    logger.debug(f"Scanning page {page_num + 1} for tables")

                    # Extract tables from this page
                    page_tables = page.find_tables(table_settings=settings)

                    for table_index, table in enumerate(page_tables):
                        # Extract table data
                        if extract_text:
                            table_data = table.extract()
                        else:
                            table_data = []

                        # Calculate dimensions
                        rows = len(table_data) if table_data else 0
                        cols = len(table_data[0]) if table_data and table_data[0] else 0

                        # Create table metadata
                        table_info = {
                            "page": page_num,
                            "table_index": table_index,
                            "bbox": table.bbox,  # (x0, top, x1, bottom)
                            "data": table_data,
                            "rows": rows,
                            "cols": cols,
                        }

                        tables.append(table_info)
                        logger.debug(
                            f"Found table on page {page_num + 1}: {rows}x{cols} at {table.bbox}"
                        )

            logger.info(f"Extracted {len(tables)} tables from {self.pdf_path.name}")
            return tables

        except Exception as e:
            logger.error(f"Error extracting tables from {self.pdf_path}: {e}", exc_info=True)
            raise

    def extract_tables_by_page(
        self, page_number: int, table_settings: dict | None = None
    ) -> list[dict]:
        """
        Extract tables from a specific page.

        Args:
            page_number: Page number (0-indexed)
            table_settings: Custom pdfplumber table detection settings

        Returns:
            list[dict]: List of tables found on the specified page
        """
        all_tables = self.extract_tables(table_settings=table_settings)
        return [t for t in all_tables if t["page"] == page_number]

    def has_tables(self) -> bool:
        """
        Check if the PDF contains any tables.

        Returns:
            bool: True if at least one table is found
        """
        try:
            tables = self.extract_tables(extract_text=False)
            return len(tables) > 0
        except Exception as e:
            logger.warning(f"Error checking for tables: {e}")
            return False

    def get_table_count(self) -> int:
        """
        Get the total number of tables in the PDF.

        Returns:
            int: Total number of tables
        """
        try:
            tables = self.extract_tables(extract_text=False)
            return len(tables)
        except Exception as e:
            logger.warning(f"Error counting tables: {e}")
            return 0

    def extract_tables_as_csv(self, output_dir: str | Path) -> list[Path]:
        """
        Extract tables and save each as a CSV file.

        Args:
            output_dir: Directory to save CSV files

        Returns:
            list[Path]: Paths to created CSV files
        """
        import csv

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        tables = self.extract_tables()
        csv_files = []

        for table in tables:
            # Generate filename: document_name_page_X_table_Y.csv
            filename = (
                f"{self.pdf_path.stem}_"
                f"page_{table['page'] + 1}_"
                f"table_{table['table_index'] + 1}.csv"
            )
            csv_path = output_dir / filename

            # Write table data to CSV
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(table["data"])

            csv_files.append(csv_path)
            logger.info(f"Saved table to {csv_path}")

        return csv_files
