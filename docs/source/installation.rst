Installation
============

Requirements
------------

* Python 3.10 or higher
* pip package manager

Basic Installation
------------------

Install the package using pip::

    pip install pdftotext-legal

Development Installation
------------------------

For development, clone the repository and install with dev dependencies::

    git clone https://github.com/fbmoulin/pdftotext.git
    cd pdftotext
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -e ".[dev]"

Optional Dependencies
---------------------

GUI Support
~~~~~~~~~~~

To use the graphical interface::

    pip install pdftotext-legal[gui]

AI Features
~~~~~~~~~~~

For image analysis with Google Gemini::

    pip install pdftotext-legal[ai]
    export GEMINI_API_KEY="your-api-key"

Build Tools
~~~~~~~~~~~

For building executables::

    pip install pdftotext-legal[build]

All Dependencies
~~~~~~~~~~~~~~~~

Install everything::

    pip install pdftotext-legal[all]

Verification
------------

Verify the installation::

    pdftotext-legal --version

Run tests::

    pytest tests/
