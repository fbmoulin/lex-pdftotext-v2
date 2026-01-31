"""Table formatting for Markdown output."""


class TableFormatter:
    """
    Format extracted tables as Markdown tables.

    Converts table data (list of lists) into properly formatted
    Markdown tables with alignment support.
    """

    @staticmethod
    def format_table(
        table_data: list[list], alignment: list[str] | None = None, include_header: bool = True
    ) -> str:
        """
        Format table data as Markdown table.

        Args:
            table_data: Table data as list of lists (rows x columns)
            alignment: List of alignment specifiers per column ('left', 'center', 'right')
            include_header: Whether first row should be treated as header

        Returns:
            str: Markdown formatted table

        Example:
            >>> data = [
            ...     ['Name', 'Age', 'City'],
            ...     ['Alice', '30', 'São Paulo'],
            ...     ['Bob', '25', 'Rio de Janeiro']
            ... ]
            >>> print(TableFormatter.format_table(data))
            | Name | Age | City |
            |---|---|---|
            | Alice | 30 | São Paulo |
            | Bob | 25 | Rio de Janeiro |
        """
        if not table_data or not table_data[0]:
            return ""

        # Determine number of columns
        num_cols = max(len(row) for row in table_data)

        # Normalize rows to have same number of columns
        normalized_data = []
        for row in table_data:
            normalized_row = list(row) + [""] * (num_cols - len(row))
            # Clean cell values (replace None with empty string)
            normalized_row = [str(cell) if cell is not None else "" for cell in normalized_row]
            normalized_data.append(normalized_row)

        # Default alignment: left for all columns
        if alignment is None:
            alignment = ["left"] * num_cols

        # Build table
        lines = []

        # First row (header or first data row)
        if normalized_data:
            lines.append(TableFormatter._format_row(normalized_data[0]))

        # Separator row (with alignment)
        lines.append(TableFormatter._format_separator(alignment))

        # Data rows (skip first row if it's a header)
        start_index = 1 if include_header else 0
        for row in normalized_data[start_index:]:
            lines.append(TableFormatter._format_row(row))

        return "\n".join(lines)

    @staticmethod
    def _format_row(row: list[str]) -> str:
        """
        Format a single table row.

        Args:
            row: List of cell values

        Returns:
            str: Markdown formatted row
        """
        # Clean and escape pipe characters in cells
        cleaned_cells = [cell.replace("|", "\\|").strip() for cell in row]
        return "| " + " | ".join(cleaned_cells) + " |"

    @staticmethod
    def _format_separator(alignment: list[str]) -> str:
        """
        Format separator row with alignment.

        Args:
            alignment: List of alignment specifiers ('left', 'center', 'right')

        Returns:
            str: Markdown separator row
        """
        separators = []
        for align in alignment:
            if align == "center":
                separators.append(":---:")
            elif align == "right":
                separators.append("---:")
            else:  # left or default
                separators.append("---")

        return "| " + " | ".join(separators) + " |"

    @staticmethod
    def format_table_with_caption(
        table_data: list[list],
        caption: str | None = None,
        page_number: int | None = None,
        table_index: int | None = None,
    ) -> str:
        """
        Format table with caption and metadata.

        Args:
            table_data: Table data as list of lists
            caption: Optional table caption
            page_number: Page number where table was found (0-indexed)
            table_index: Index of table on the page

        Returns:
            str: Markdown formatted table with caption
        """
        sections = []

        # Generate caption if not provided
        if caption is None and page_number is not None:
            caption = "Tabela"
            if page_number is not None:
                caption += f" - Página {page_number + 1}"
            if table_index is not None:
                caption += f" (Tabela {table_index + 1})"

        # Add caption
        if caption:
            sections.append(f"**{caption}**\n")

        # Add table
        table_md = TableFormatter.format_table(table_data)
        sections.append(table_md)

        return "\n".join(sections)

    @staticmethod
    def format_all_tables(tables: list[dict], include_metadata: bool = True) -> str:
        """
        Format multiple tables as Markdown.

        Args:
            tables: List of table dictionaries from TableExtractor
            include_metadata: Whether to include table metadata (page, position)

        Returns:
            str: Markdown formatted tables
        """
        if not tables:
            return ""

        formatted_tables = []

        for table in tables:
            if include_metadata:
                # Format with caption
                table_md = TableFormatter.format_table_with_caption(
                    table["data"], page_number=table["page"], table_index=table["table_index"]
                )
            else:
                # Format without metadata
                table_md = TableFormatter.format_table(table["data"])

            formatted_tables.append(table_md)

        # Join tables with double newline
        return "\n\n".join(formatted_tables)

    @staticmethod
    def detect_alignment(table_data: list[list]) -> list[str]:
        """
        Auto-detect column alignment based on content.

        Heuristic:
        - If column contains mostly numbers: right-align
        - Otherwise: left-align

        Args:
            table_data: Table data as list of lists

        Returns:
            list[str]: List of alignment specifiers
        """
        if not table_data or not table_data[0]:
            return []

        num_cols = max(len(row) for row in table_data)
        alignments = []

        for col_idx in range(num_cols):
            # Get all values in this column
            col_values = []
            for row in table_data:
                if col_idx < len(row) and row[col_idx] is not None:
                    col_values.append(str(row[col_idx]).strip())

            # Check if mostly numeric
            numeric_count = 0
            for value in col_values:
                # Remove common formatting (currency, commas, etc.)
                cleaned = value.replace("R$", "").replace(".", "").replace(",", "").strip()
                if cleaned.replace("-", "").isdigit():
                    numeric_count += 1

            # If >50% numeric, right-align
            if col_values and numeric_count / len(col_values) > 0.5:
                alignments.append("right")
            else:
                alignments.append("left")

        return alignments
