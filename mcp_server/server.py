#!/usr/bin/env python3
"""MCP Server for PDF Legal Extractor - Brazilian legal document processing."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import pdftotext modules
from lex_pdftotext.extractors.pymupdf_extractor import PyMuPDFExtractor
from lex_pdftotext.processors.metadata_parser import MetadataParser
from lex_pdftotext.processors.text_normalizer import TextNormalizer
from lex_pdftotext.formatters.markdown_formatter import MarkdownFormatter
from lex_pdftotext.formatters.index_generator import IndexGenerator
from lex_pdftotext.utils.patterns import RegexPatterns

app = Server("pdf-legal-extractor")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for PDF legal extraction."""
    return [
        Tool(
            name="extract_legal_pdf",
            description="Extrai texto de PDF jurídico brasileiro (PJe) com metadados, normalização e índice de peças processuais",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Caminho absoluto para o arquivo PDF"
                    },
                    "indexed": {
                        "type": "boolean",
                        "description": "Gerar índice de peças processuais com cross-references (default: true)",
                        "default": True
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Incluir metadados (processo, partes, advogados)",
                        "default": True
                    },
                    "normalize": {
                        "type": "boolean",
                        "description": "Normalizar texto (converter MAIÚSCULAS, limpar ruído)",
                        "default": True
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="extract_metadata_only",
            description="Extrai apenas metadados de PDF jurídico (número do processo, partes, advogados, IDs de documentos)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Caminho absoluto para o arquivo PDF"
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="list_document_ids",
            description="Lista todos os IDs de documentos (Num. XXXXXXXX) encontrados no PDF com suas posições",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Caminho absoluto para o arquivo PDF"
                    }
                },
                "required": ["pdf_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool call."""

    if name == "extract_legal_pdf":
        return await extract_legal_pdf(
            arguments["pdf_path"],
            arguments.get("indexed", True),
            arguments.get("include_metadata", True),
            arguments.get("normalize", True)
        )

    elif name == "extract_metadata_only":
        return await extract_metadata_only(arguments["pdf_path"])

    elif name == "list_document_ids":
        return await list_document_ids(arguments["pdf_path"])

    else:
        return [TextContent(type="text", text=f"Ferramenta desconhecida: {name}")]


async def extract_legal_pdf(
    pdf_path: str,
    indexed: bool = True,
    include_metadata: bool = True,
    normalize: bool = True
) -> list[TextContent]:
    """Extract text from a Brazilian legal PDF."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return [TextContent(type="text", text=f"❌ Arquivo não encontrado: {pdf_path}")]

        if not path.suffix.lower() == ".pdf":
            return [TextContent(type="text", text=f"❌ Arquivo não é PDF: {pdf_path}")]

        # Extract text
        extractor = PyMuPDFExtractor()
        raw_text = extractor.extract(str(path))

        if not raw_text or not raw_text.strip():
            return [TextContent(type="text", text="❌ PDF não contém texto extraível (pode ser escaneado)")]

        # Extract document positions from raw text before normalization
        document_positions = []
        if indexed:
            document_positions = RegexPatterns.extract_document_ids_with_positions(raw_text)

        # Normalize text if requested
        text = raw_text
        if normalize:
            normalizer = TextNormalizer()
            text = normalizer.normalize(raw_text)

        # Parse metadata
        metadata = None
        if include_metadata:
            parser = MetadataParser()
            metadata = parser.parse(raw_text)  # Use raw text for metadata extraction
            metadata.document_positions = document_positions

        # Format output
        formatter = MarkdownFormatter()

        if indexed and metadata:
            output = formatter.format_with_index(text, metadata)
        elif include_metadata and metadata:
            output = formatter.format(text, metadata, include_metadata=True)
        else:
            output = formatter.format(text, metadata, include_metadata=False)

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro na extração: {str(e)}")]


async def extract_metadata_only(pdf_path: str) -> list[TextContent]:
    """Extract only metadata from a PDF."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return [TextContent(type="text", text=f"❌ Arquivo não encontrado: {pdf_path}")]

        extractor = PyMuPDFExtractor()
        raw_text = extractor.extract(str(path))

        if not raw_text:
            return [TextContent(type="text", text="❌ PDF não contém texto extraível")]

        parser = MetadataParser()
        metadata = parser.parse(raw_text)

        result = {
            "processo": metadata.process_number,
            "autor": metadata.author,
            "reu": metadata.defendant,
            "vara": metadata.court,
            "valor_causa": metadata.case_value,
            "advogados": metadata.lawyers,
            "tipo_documento": metadata.document_type,
            "ids_documentos": metadata.document_ids,
            "assinaturas": metadata.signatures
        }

        output = "## Metadados do Processo\n\n"
        output += f"**Processo:** {result['processo'] or 'Não identificado'}\n"
        output += f"**Autor:** {result['autor'] or 'Não identificado'}\n"
        output += f"**Réu:** {result['reu'] or 'Não identificado'}\n"
        output += f"**Vara:** {result['vara'] or 'Não identificado'}\n"
        output += f"**Valor da Causa:** {result['valor_causa'] or 'Não informado'}\n"
        output += f"**Tipo de Documento:** {result['tipo_documento'] or 'Não identificado'}\n\n"

        if result['advogados']:
            output += "### Advogados\n"
            for adv in result['advogados']:
                output += f"- {adv}\n"
            output += "\n"

        if result['ids_documentos']:
            output += f"### IDs de Documentos ({len(result['ids_documentos'])})\n"
            for doc_id in result['ids_documentos'][:20]:  # Limit to 20
                output += f"- {doc_id}\n"
            if len(result['ids_documentos']) > 20:
                output += f"- ... e mais {len(result['ids_documentos']) - 20} documentos\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro: {str(e)}")]


async def list_document_ids(pdf_path: str) -> list[TextContent]:
    """List all document IDs with their positions."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return [TextContent(type="text", text=f"❌ Arquivo não encontrado: {pdf_path}")]

        extractor = PyMuPDFExtractor()
        raw_text = extractor.extract(str(path))

        if not raw_text:
            return [TextContent(type="text", text="❌ PDF não contém texto extraível")]

        positions = RegexPatterns.extract_document_ids_with_positions(raw_text)

        if not positions:
            return [TextContent(type="text", text="Nenhum ID de documento encontrado (formato: Num. XXXXXXXX)")]

        index_gen = IndexGenerator()

        output = f"## IDs de Documentos Encontrados ({len(positions)})\n\n"
        output += "| ID | Linha | Tipo Detectado | Contexto |\n"
        output += "|-----|-------|----------------|----------|\n"

        for pos in positions:
            doc_type = index_gen.detect_type(pos.get("context_before", ""), pos.get("context_after", ""))
            icon = index_gen.get_icon(doc_type)
            context = pos.get("context_before", "")[-30:] if pos.get("context_before") else ""
            output += f"| {pos['id']} | {pos['line']} | {icon} {doc_type} | ...{context} |\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
