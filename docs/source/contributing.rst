Contributing
============

We welcome contributions! This guide will help you get started.

Development Setup
-----------------

1. Fork and clone the repository::

    git clone https://github.com/fbmoulin/pdftotext.git
    cd pdftotext

2. Create a virtual environment::

    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install development dependencies::

    pip install -e ".[dev]"

4. Install pre-commit hooks::

    pre-commit install

Code Quality Standards
----------------------

Type Hints
~~~~~~~~~~

All code must have type hints::

    def process_text(text: str, metadata: DocumentMetadata | None = None) -> str:
        """Process text with optional metadata."""
        ...

Testing
~~~~~~~

Write tests for all new features::

    def test_my_feature():
        """Test my new feature."""
        result = my_feature("input")
        assert result == "expected"

Aim for 80%+ coverage::

    pytest --cov=src tests/

Documentation
~~~~~~~~~~~~~

Add docstrings to all public methods::

    def extract_tables(self, table_settings: dict | None = None) -> list[dict]:
        """
        Extract all tables from the PDF.

        Args:
            table_settings: Custom pdfplumber table detection settings

        Returns:
            List of extracted tables with metadata

        Example:
            >>> extractor = TableExtractor('doc.pdf')
            >>> tables = extractor.extract_tables()
        """

Code Style
----------

We use the following tools:

* **Black**: Code formatting
* **isort**: Import sorting
* **Ruff**: Linting
* **MyPy**: Type checking

Run all checks::

    black src/ tests/
    isort src/ tests/
    ruff check src/ tests/
    mypy src/

Pre-commit hooks will run these automatically.

Testing Guidelines
------------------

Running Tests
~~~~~~~~~~~~~

Run all tests::

    pytest tests/

Run specific test::

    pytest tests/test_extraction.py::TestTextNormalizer::test_normalize

Run with coverage::

    pytest --cov=src --cov-report=html tests/

Writing Tests
~~~~~~~~~~~~~

1. Use descriptive test names
2. One assertion per test when possible
3. Use fixtures for common setup
4. Mock external dependencies

Example::

    import pytest
    from unittest.mock import MagicMock, patch

    @pytest.fixture
    def sample_pdf_path(tmp_path):
        """Create a sample PDF for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")
        return pdf_file

    @patch("fitz.open")
    def test_extraction(mock_fitz_open, sample_pdf_path):
        """Test PDF text extraction."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value.__enter__.return_value = mock_doc

        # Your test here
        assert True

Pull Request Process
--------------------

1. **Create a feature branch**::

    git checkout -b feature/my-feature

2. **Make your changes** with meaningful commits

3. **Add tests** for new functionality

4. **Update documentation** if needed

5. **Run all checks**::

    pytest tests/
    mypy src/
    black src/ tests/
    ruff check src/

6. **Push and create PR**::

    git push origin feature/my-feature

7. **Fill in PR template** with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots (if UI changes)

Commit Messages
---------------

Follow conventional commits::

    feat: Add table extraction feature
    fix: Handle empty PDF pages correctly
    docs: Update installation guide
    test: Add tests for metadata parser
    chore: Update dependencies

Project Structure
-----------------

::

    pdftotext/
    ├── src/
    │   ├── extractors/     # PDF extraction
    │   ├── processors/     # Text processing
    │   ├── formatters/     # Output formatting
    │   └── utils/          # Shared utilities
    ├── tests/              # Test suite
    ├── docs/               # Documentation
    ├── main.py             # CLI entry point
    └── pyproject.toml      # Project config

Adding New Features
-------------------

Extractors
~~~~~~~~~~

1. Inherit from ``PDFExtractor`` base class
2. Implement required methods
3. Add comprehensive tests
4. Update documentation

Formatters
~~~~~~~~~~

1. Create new class in ``src/formatters/``
2. Implement ``format()`` method
3. Add ``save_to_file()`` static method
4. Write tests and docs

Utilities
~~~~~~~~~

1. Add to appropriate ``src/utils/`` module
2. Include type hints
3. Write unit tests
4. Document with examples

Reporting Issues
----------------

When reporting bugs, include:

* Python version
* Package version
* Minimal reproduction code
* Error messages/stack traces
* Expected vs actual behavior

Feature requests should include:

* Use case description
* Proposed API/interface
* Examples of how it would be used

Community Guidelines
--------------------

* Be respectful and inclusive
* Help others learn
* Give constructive feedback
* Celebrate contributions

Questions?
----------

* Open an issue for bugs or features
* Start a discussion for questions
* Check existing issues first

Thank you for contributing!
