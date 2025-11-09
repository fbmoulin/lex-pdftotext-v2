"""Tests for table extraction and formatting."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.formatters.table_formatter import TableFormatter


class TestTableFormatterBasic:
    """Test basic table formatting functionality."""

    def test_format_simple_table(self):
        """Test formatting a simple table."""
        formatter = TableFormatter()
        data = [
            ["Name", "Age", "City"],
            ["Alice", "30", "São Paulo"],
            ["Bob", "25", "Rio de Janeiro"],
        ]

        result = formatter.format_table(data)

        # Check structure
        assert "| Name | Age | City |" in result
        assert "| --- | --- | --- |" in result
        assert "| Alice | 30 | São Paulo |" in result
        assert "| Bob | 25 | Rio de Janeiro |" in result

    def test_format_table_without_header(self):
        """Test formatting table without header row."""
        formatter = TableFormatter()
        data = [["Alice", "30", "São Paulo"], ["Bob", "25", "Rio de Janeiro"]]

        result = formatter.format_table(data, include_header=False)

        # Should still have separator after first row
        assert "| --- | --- | --- |" in result
        assert "| Alice | 30 | São Paulo |" in result

    def test_format_table_with_alignment(self):
        """Test formatting with custom alignment."""
        formatter = TableFormatter()
        data = [["Name", "Value", "Status"], ["Item1", "100", "Active"]]

        result = formatter.format_table(data, alignment=["left", "right", "center"])

        # Check alignment markers
        assert "| --- | ---: | :---: |" in result

    def test_format_empty_table(self):
        """Test formatting empty table."""
        formatter = TableFormatter()

        result = formatter.format_table([])

        assert result == ""

    def test_format_table_with_none_values(self):
        """Test formatting table with None values."""
        formatter = TableFormatter()
        data = [["Name", "Value"], ["Item1", None], [None, "200"]]

        result = formatter.format_table(data)

        # None should be converted to empty string
        assert "| Item1 |  |" in result
        assert "|  | 200 |" in result

    def test_format_table_uneven_rows(self):
        """Test formatting table with rows of different lengths."""
        formatter = TableFormatter()
        data = [["A", "B", "C"], ["1", "2"], ["3", "4", "5", "6"]]

        result = formatter.format_table(data)

        # Should normalize to same number of columns
        lines = result.strip().split("\n")
        # All lines should have same number of pipes
        pipe_counts = [line.count("|") for line in lines]
        assert len(set(pipe_counts)) == 1  # All equal

    def test_format_table_escapes_pipes(self):
        """Test formatting escapes pipe characters in cells."""
        formatter = TableFormatter()
        data = [["Column | with | pipes"], ["Cell | value"]]

        result = formatter.format_table(data)

        # Pipes should be escaped
        assert "\\|" in result
        assert result.count("|") > result.count("\\|")  # More unescaped than escaped


class TestTableFormatterWithCaption:
    """Test table formatting with captions."""

    def test_format_with_custom_caption(self):
        """Test formatting with custom caption."""
        formatter = TableFormatter()
        data = [["Name", "Value"], ["Item", "100"]]

        result = formatter.format_table_with_caption(data, caption="Custom Table Title")

        assert "**Custom Table Title**" in result
        assert "| Name | Value |" in result

    def test_format_with_page_number(self):
        """Test formatting with page number metadata."""
        formatter = TableFormatter()
        data = [["A", "B"], ["1", "2"]]

        result = formatter.format_table_with_caption(data, page_number=5, table_index=2)

        assert "**Tabela - Página 6 (Tabela 3)**" in result
        # 0-indexed, so page 5 = page 6, table 2 = table 3

    def test_format_without_caption_or_metadata(self):
        """Test formatting without any caption or metadata."""
        formatter = TableFormatter()
        data = [["A", "B"], ["1", "2"]]

        result = formatter.format_table_with_caption(data)

        # Should have just the table, no caption
        assert "| A | B |" in result
        assert "**" not in result or result.count("**") == 0


class TestTableFormatterMultipleTables:
    """Test formatting multiple tables."""

    def test_format_all_tables(self):
        """Test formatting multiple tables."""
        formatter = TableFormatter()
        tables = [
            {
                "page": 0,
                "table_index": 0,
                "data": [["Name", "Age"], ["Alice", "30"]],
                "rows": 2,
                "cols": 2,
                "bbox": (0, 0, 100, 100),
            },
            {
                "page": 1,
                "table_index": 0,
                "data": [["City", "Country"], ["Paris", "France"]],
                "rows": 2,
                "cols": 2,
                "bbox": (0, 0, 100, 100),
            },
        ]

        result = formatter.format_all_tables(tables, include_metadata=True)

        # Should have both tables
        assert "Alice" in result
        assert "Paris" in result
        assert "**Tabela - Página 1 (Tabela 1)**" in result
        assert "**Tabela - Página 2 (Tabela 1)**" in result

    def test_format_all_tables_without_metadata(self):
        """Test formatting multiple tables without metadata."""
        formatter = TableFormatter()
        tables = [
            {
                "page": 0,
                "table_index": 0,
                "data": [["A", "B"], ["1", "2"]],
                "rows": 2,
                "cols": 2,
                "bbox": (0, 0, 100, 100),
            }
        ]

        result = formatter.format_all_tables(tables, include_metadata=False)

        # Should not have metadata
        assert "**Tabela" not in result
        assert "| A | B |" in result

    def test_format_all_tables_empty_list(self):
        """Test formatting empty table list."""
        formatter = TableFormatter()

        result = formatter.format_all_tables([])

        assert result == ""


class TestTableFormatterAlignment:
    """Test automatic alignment detection."""

    def test_detect_alignment_numeric_columns(self):
        """Test alignment detection identifies numeric columns."""
        formatter = TableFormatter()
        data = [
            ["Name", "Price", "Quantity"],
            ["Item1", "100.50", "5"],
            ["Item2", "200.00", "10"],
            ["Item3", "50.25", "3"],
        ]

        alignments = formatter.detect_alignment(data)

        # First column (Name) should be left
        # Second and third columns (numbers) should be right
        assert alignments[0] == "left"
        assert alignments[1] == "right"
        assert alignments[2] == "right"

    def test_detect_alignment_currency_values(self):
        """Test alignment detection handles currency."""
        formatter = TableFormatter()
        data = [["Product", "Value"], ["A", "R$ 1.000,00"], ["B", "R$ 500,50"]]

        alignments = formatter.detect_alignment(data)

        # Currency column should be detected as numeric (right)
        assert alignments[1] == "right"

    def test_detect_alignment_mixed_columns(self):
        """Test alignment with mixed content."""
        formatter = TableFormatter()
        data = [["Text", "Mixed"], ["Hello", "123"], ["World", "abc"]]

        alignments = formatter.detect_alignment(data)

        # First column: all text = left
        # Second column: 50/50 = left (not >50% numeric)
        assert alignments[0] == "left"
        assert alignments[1] == "left"

    def test_detect_alignment_empty_table(self):
        """Test alignment detection with empty table."""
        formatter = TableFormatter()

        alignments = formatter.detect_alignment([])

        assert alignments == []

    def test_detect_alignment_with_negative_numbers(self):
        """Test alignment detection handles negative numbers."""
        formatter = TableFormatter()
        data = [["Value"], ["-100"], ["-50.5"], ["200"]]

        alignments = formatter.detect_alignment(data)

        # Should detect as numeric despite negatives
        assert alignments[0] == "right"


class TestTableFormatterEdgeCases:
    """Test edge cases and special scenarios."""

    def test_format_single_cell_table(self):
        """Test formatting table with single cell."""
        formatter = TableFormatter()
        data = [["Single"]]

        result = formatter.format_table(data)

        assert "| Single |" in result
        assert "| --- |" in result

    def test_format_single_row_table(self):
        """Test formatting table with single row."""
        formatter = TableFormatter()
        data = [["A", "B", "C"]]

        result = formatter.format_table(data)

        # Should have header and separator
        lines = result.strip().split("\n")
        assert len(lines) == 2  # Header + separator

    def test_format_table_with_whitespace(self):
        """Test formatting preserves and trims whitespace correctly."""
        formatter = TableFormatter()
        data = [["  Name  ", "Value"], ["Item", "  100  "]]

        result = formatter.format_table(data)

        # Whitespace should be trimmed
        assert "| Name | Value |" in result
        assert "| Item | 100 |" in result

    def test_format_table_with_special_characters(self):
        """Test formatting with special characters."""
        formatter = TableFormatter()
        data = [["Name", "Email"], ["João", "joao@example.com"], ["María", "maria@test.com"]]

        result = formatter.format_table(data)

        # Should preserve unicode
        assert "João" in result
        assert "María" in result
        assert "@" in result

    def test_format_table_with_long_content(self):
        """Test formatting with long cell content."""
        formatter = TableFormatter()
        data = [["Short", "Very long content that spans multiple words and characters"], ["A", "B"]]

        result = formatter.format_table(data)

        # Should handle long content
        assert "Very long content" in result
        assert "| Short |" in result

    def test_format_all_tables_separates_tables(self):
        """Test multiple tables are properly separated."""
        formatter = TableFormatter()
        tables = [
            {
                "page": 0,
                "table_index": 0,
                "data": [["A"], ["1"]],
                "rows": 2,
                "cols": 1,
                "bbox": (0, 0, 100, 100),
            },
            {
                "page": 0,
                "table_index": 1,
                "data": [["B"], ["2"]],
                "rows": 2,
                "cols": 1,
                "bbox": (0, 0, 100, 100),
            },
        ]

        result = formatter.format_all_tables(tables)

        # Tables should be separated by double newline
        assert "\n\n" in result

        # Should have both tables
        assert "| A |" in result
        assert "| B |" in result
