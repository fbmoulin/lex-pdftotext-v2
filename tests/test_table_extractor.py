"""Tests for table extractor functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.extractors.table_extractor import TableExtractor
from src.utils.exceptions import InvalidPathError


class TestTableExtractorInit:
    """Test TableExtractor initialization."""

    def test_init_with_valid_pdf_path(self, tmp_path):
        """Test initialization with valid PDF path."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = TableExtractor(pdf_file)

        assert extractor.pdf_path == pdf_file
        assert extractor.pdf_path.exists()

    def test_init_with_str_path(self, tmp_path):
        """Test initialization with string path."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = TableExtractor(str(pdf_file))

        assert isinstance(extractor.pdf_path, Path)
        assert extractor.pdf_path.exists()

    def test_init_file_not_found(self, tmp_path):
        """Test initialization fails for non-existent file."""
        pdf_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(InvalidPathError, match="Arquivo não encontrado"):
            TableExtractor(pdf_file)

    def test_init_not_pdf_file(self, tmp_path):
        """Test initialization fails for non-PDF file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")

        with pytest.raises(InvalidPathError, match="Arquivo deve ser PDF"):
            TableExtractor(txt_file)

    def test_init_pdf_uppercase_extension(self, tmp_path):
        """Test initialization accepts .PDF extension (uppercase)."""
        pdf_file = tmp_path / "test.PDF"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = TableExtractor(pdf_file)

        assert extractor.pdf_path == pdf_file


class TestTableExtractorExtractTables:
    """Test extract_tables() method."""

    @patch("pdfplumber.open")
    def test_extract_tables_with_one_table(self, mock_pdfplumber_open, tmp_path):
        """Test extraction of single table from PDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        tables = extractor.extract_tables()

        assert len(tables) == 1
        assert tables[0]["page"] == 0
        assert tables[0]["table_index"] == 0
        assert tables[0]["bbox"] == (10, 20, 100, 80)
        assert tables[0]["rows"] == 3
        assert tables[0]["cols"] == 2
        assert tables[0]["data"] == [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]

    @patch("pdfplumber.open")
    def test_extract_tables_multiple_tables(self, mock_pdfplumber_open, tmp_path):
        """Test extraction of multiple tables from PDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock two tables on one page
        mock_pdf = MagicMock()
        mock_page = MagicMock()

        mock_table1 = MagicMock()
        mock_table1.bbox = (10, 20, 100, 80)
        mock_table1.extract.return_value = [["A", "B"], ["1", "2"]]

        mock_table2 = MagicMock()
        mock_table2.bbox = (10, 100, 100, 150)
        mock_table2.extract.return_value = [["X", "Y"], ["3", "4"]]

        mock_page.find_tables.return_value = [mock_table1, mock_table2]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        tables = extractor.extract_tables()

        assert len(tables) == 2
        assert tables[0]["table_index"] == 0
        assert tables[1]["table_index"] == 1
        assert tables[0]["data"] == [["A", "B"], ["1", "2"]]
        assert tables[1]["data"] == [["X", "Y"], ["3", "4"]]

    @patch("pdfplumber.open")
    def test_extract_tables_multiple_pages(self, mock_pdfplumber_open, tmp_path):
        """Test extraction from multiple pages."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock tables on different pages
        mock_pdf = MagicMock()

        mock_page1 = MagicMock()
        mock_table1 = MagicMock()
        mock_table1.bbox = (10, 20, 100, 80)
        mock_table1.extract.return_value = [["Page1"]]
        mock_page1.find_tables.return_value = [mock_table1]

        mock_page2 = MagicMock()
        mock_table2 = MagicMock()
        mock_table2.bbox = (10, 20, 100, 80)
        mock_table2.extract.return_value = [["Page2"]]
        mock_page2.find_tables.return_value = [mock_table2]

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        tables = extractor.extract_tables()

        assert len(tables) == 2
        assert tables[0]["page"] == 0
        assert tables[1]["page"] == 1
        assert tables[0]["data"] == [["Page1"]]
        assert tables[1]["data"] == [["Page2"]]

    @patch("pdfplumber.open")
    def test_extract_tables_no_tables(self, mock_pdfplumber_open, tmp_path):
        """Test extraction when PDF has no tables."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.find_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        tables = extractor.extract_tables()

        assert len(tables) == 0
        assert tables == []

    @patch("pdfplumber.open")
    def test_extract_tables_without_text(self, mock_pdfplumber_open, tmp_path):
        """Test extraction without extracting text content."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = [["A", "B"]]

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        tables = extractor.extract_tables(extract_text=False)

        assert len(tables) == 1
        assert tables[0]["data"] == []  # No text extracted
        assert tables[0]["rows"] == 0
        assert tables[0]["cols"] == 0
        # extract() should not be called when extract_text=False
        mock_table.extract.assert_not_called()

    @patch("pdfplumber.open")
    def test_extract_tables_custom_settings(self, mock_pdfplumber_open, tmp_path):
        """Test extraction with custom table settings."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = [["A"]]

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        custom_settings = {"snap_tolerance": 5, "join_tolerance": 5}
        extractor.extract_tables(table_settings=custom_settings)

        # Verify custom settings were passed
        call_args = mock_page.find_tables.call_args
        assert call_args[1]["table_settings"]["snap_tolerance"] == 5
        assert call_args[1]["table_settings"]["join_tolerance"] == 5

    @patch("pdfplumber.open")
    def test_extract_tables_empty_table_data(self, mock_pdfplumber_open, tmp_path):
        """Test extraction when table.extract() returns empty data."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = []  # Empty table

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        tables = extractor.extract_tables()

        assert len(tables) == 1
        assert tables[0]["rows"] == 0
        assert tables[0]["cols"] == 0
        assert tables[0]["data"] == []

    @patch("pdfplumber.open")
    def test_extract_tables_error_handling(self, mock_pdfplumber_open, tmp_path):
        """Test error handling during extraction."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdfplumber_open.side_effect = Exception("PDF corrupted")

        extractor = TableExtractor(pdf_file)

        with pytest.raises(Exception, match="PDF corrupted"):
            extractor.extract_tables()


class TestTableExtractorExtractTablesByPage:
    """Test extract_tables_by_page() method."""

    @patch("pdfplumber.open")
    def test_extract_tables_by_page_single_page(self, mock_pdfplumber_open, tmp_path):
        """Test extraction from specific page."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock 2 pages, each with a table
        mock_pdf = MagicMock()

        mock_page1 = MagicMock()
        mock_table1 = MagicMock()
        mock_table1.bbox = (10, 20, 100, 80)
        mock_table1.extract.return_value = [["Page 0 Table"]]
        mock_page1.find_tables.return_value = [mock_table1]

        mock_page2 = MagicMock()
        mock_table2 = MagicMock()
        mock_table2.bbox = (10, 20, 100, 80)
        mock_table2.extract.return_value = [["Page 1 Table"]]
        mock_page2.find_tables.return_value = [mock_table2]

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        page_0_tables = extractor.extract_tables_by_page(0)

        assert len(page_0_tables) == 1
        assert page_0_tables[0]["page"] == 0
        assert page_0_tables[0]["data"] == [["Page 0 Table"]]

    @patch("pdfplumber.open")
    def test_extract_tables_by_page_no_tables_on_page(self, mock_pdfplumber_open, tmp_path):
        """Test extraction from page with no tables."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()

        mock_page1 = MagicMock()
        mock_table1 = MagicMock()
        mock_table1.bbox = (10, 20, 100, 80)
        mock_table1.extract.return_value = [["Data"]]
        mock_page1.find_tables.return_value = [mock_table1]

        mock_page2 = MagicMock()
        mock_page2.find_tables.return_value = []  # No tables

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        page_1_tables = extractor.extract_tables_by_page(1)

        assert len(page_1_tables) == 0


class TestTableExtractorHasTables:
    """Test has_tables() method."""

    @patch("pdfplumber.open")
    def test_has_tables_returns_true(self, mock_pdfplumber_open, tmp_path):
        """Test has_tables returns True when tables exist."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)

        assert extractor.has_tables() is True

    @patch("pdfplumber.open")
    def test_has_tables_returns_false(self, mock_pdfplumber_open, tmp_path):
        """Test has_tables returns False when no tables exist."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.find_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)

        assert extractor.has_tables() is False

    @patch("pdfplumber.open")
    def test_has_tables_handles_errors(self, mock_pdfplumber_open, tmp_path):
        """Test has_tables returns False on errors."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdfplumber_open.side_effect = Exception("Error")

        extractor = TableExtractor(pdf_file)

        assert extractor.has_tables() is False


class TestTableExtractorGetTableCount:
    """Test get_table_count() method."""

    @patch("pdfplumber.open")
    def test_get_table_count_with_tables(self, mock_pdfplumber_open, tmp_path):
        """Test table count with multiple tables."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()

        mock_table1 = MagicMock()
        mock_table1.bbox = (10, 20, 100, 80)
        mock_table2 = MagicMock()
        mock_table2.bbox = (10, 100, 100, 150)

        mock_page.find_tables.return_value = [mock_table1, mock_table2]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)

        assert extractor.get_table_count() == 2

    @patch("pdfplumber.open")
    def test_get_table_count_no_tables(self, mock_pdfplumber_open, tmp_path):
        """Test table count returns 0 when no tables."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.find_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)

        assert extractor.get_table_count() == 0

    @patch("pdfplumber.open")
    def test_get_table_count_handles_errors(self, mock_pdfplumber_open, tmp_path):
        """Test table count returns 0 on errors."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_pdfplumber_open.side_effect = Exception("Error")

        extractor = TableExtractor(pdf_file)

        assert extractor.get_table_count() == 0


class TestTableExtractorExtractTablesAsCSV:
    """Test extract_tables_as_csv() method."""

    @patch("pdfplumber.open")
    def test_extract_tables_as_csv_creates_files(self, mock_pdfplumber_open, tmp_path):
        """Test CSV export creates files correctly."""
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")
        output_dir = tmp_path / "output"

        # Mock table data
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        csv_files = extractor.extract_tables_as_csv(output_dir)

        assert len(csv_files) == 1
        assert csv_files[0].exists()
        assert csv_files[0].suffix == ".csv"
        assert "document_page_1_table_1.csv" in csv_files[0].name

        # Verify CSV content
        content = csv_files[0].read_text()
        assert "Name,Age" in content
        assert "Alice,30" in content
        assert "Bob,25" in content

    @patch("pdfplumber.open")
    def test_extract_tables_as_csv_multiple_tables(self, mock_pdfplumber_open, tmp_path):
        """Test CSV export with multiple tables."""
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")
        output_dir = tmp_path / "output"

        # Mock two tables
        mock_pdf = MagicMock()
        mock_page = MagicMock()

        mock_table1 = MagicMock()
        mock_table1.bbox = (10, 20, 100, 80)
        mock_table1.extract.return_value = [["A"], ["1"]]

        mock_table2 = MagicMock()
        mock_table2.bbox = (10, 100, 100, 150)
        mock_table2.extract.return_value = [["B"], ["2"]]

        mock_page.find_tables.return_value = [mock_table1, mock_table2]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        csv_files = extractor.extract_tables_as_csv(output_dir)

        assert len(csv_files) == 2
        assert all(f.exists() for f in csv_files)
        assert "table_1.csv" in csv_files[0].name
        assert "table_2.csv" in csv_files[1].name

    @patch("pdfplumber.open")
    def test_extract_tables_as_csv_creates_output_dir(self, mock_pdfplumber_open, tmp_path):
        """Test CSV export creates output directory if it doesn't exist."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")
        output_dir = tmp_path / "new" / "nested" / "dir"

        # Mock table
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = [["A"], ["1"]]

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        csv_files = extractor.extract_tables_as_csv(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()
        assert len(csv_files) == 1

    @patch("pdfplumber.open")
    def test_extract_tables_as_csv_no_tables(self, mock_pdfplumber_open, tmp_path):
        """Test CSV export when no tables exist."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")
        output_dir = tmp_path / "output"

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.find_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        csv_files = extractor.extract_tables_as_csv(output_dir)

        assert len(csv_files) == 0

    @patch("pdfplumber.open")
    def test_extract_tables_as_csv_with_str_output_dir(self, mock_pdfplumber_open, tmp_path):
        """Test CSV export accepts string output directory."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")
        output_dir = tmp_path / "output"

        # Mock table
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.bbox = (10, 20, 100, 80)
        mock_table.extract.return_value = [["A"], ["1"]]

        mock_page.find_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = TableExtractor(pdf_file)
        csv_files = extractor.extract_tables_as_csv(str(output_dir))

        assert len(csv_files) == 1
        assert csv_files[0].exists()
