"""Image analysis using Google Gemini API."""

import os
import io
import base64
from typing import Optional
from PIL import Image


class ImageAnalyzer:
    """
    Analyze images using Google Gemini Vision API.

    Generates contextual descriptions of images found in legal documents,
    identifying evidence, exhibits, signatures, stamps, etc.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize image analyzer with Gemini API.

        Args:
            api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)

        Raises:
            ValueError: If no API key is found
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Lazy import to avoid requiring google-generativeai if not using images
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=self.api_key)
            self.model = self.genai.GenerativeModel('gemini-1.5-flash')
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )

    def describe_image(
        self,
        image: Image.Image,
        context: str = "legal document",
        page_num: Optional[int] = None
    ) -> str:
        """
        Generate a description of an image using Gemini Vision.

        Args:
            image: PIL Image object to analyze
            context: Context about the document (e.g., "legal petition", "court decision")
            page_num: Page number where image appears (optional)

        Returns:
            str: Description of the image in Portuguese
        """
        # Build prompt
        prompt = self._build_prompt(context, page_num)

        try:
            # Convert PIL Image to format Gemini accepts
            # Gemini can handle PIL Image directly
            response = self.model.generate_content([prompt, image])

            # Extract text from response
            description = response.text.strip()

            return description

        except Exception as e:
            return f"[Erro ao analisar imagem: {str(e)}]"

    def describe_images_batch(
        self,
        images: list[dict],
        context: str = "legal document"
    ) -> list[dict]:
        """
        Analyze multiple images in batch.

        Args:
            images: List of image dicts (from PyMuPDFExtractor.extract_images())
            context: Document context

        Returns:
            list[dict]: Images with added 'description' field
        """
        results = []

        for img_data in images:
            try:
                description = self.describe_image(
                    img_data['image'],
                    context=context,
                    page_num=img_data['page_num']
                )

                # Add description to image data
                img_data_copy = img_data.copy()
                img_data_copy['description'] = description
                results.append(img_data_copy)

            except Exception as e:
                # Add error as description
                img_data_copy = img_data.copy()
                img_data_copy['description'] = f"[Erro: {str(e)}]"
                results.append(img_data_copy)

        return results

    def _build_prompt(self, context: str, page_num: Optional[int] = None) -> str:
        """
        Build prompt for Gemini vision analysis.

        Args:
            context: Document context
            page_num: Page number (optional)

        Returns:
            str: Formatted prompt in Portuguese
        """
        page_info = f" (página {page_num})" if page_num else ""

        prompt = f"""Analise esta imagem encontrada em um {context}{page_info} e forneça uma descrição detalhada em português.

Identifique:
1. **Tipo de conteúdo**: Documento digitalizado, foto, diagrama, assinatura, carimbo, etc.
2. **Elementos visuais principais**: O que está sendo mostrado
3. **Texto visível**: Transcreva textos legíveis (se houver)
4. **Relevância jurídica**: Se for uma prova, evidência, ou documento anexo, explique sua possível importância
5. **Qualidade**: Mencione se a imagem está legível, borrada, ou tem problemas de qualidade

Seja conciso mas informativo. Foque em detalhes que seriam relevantes para análise jurídica.

Formato da resposta:
**Tipo:** [tipo do conteúdo]
**Descrição:** [descrição detalhada]
**Texto visível:** [transcrição se aplicável]
**Observações:** [qualidade e relevância]
"""

        return prompt


def format_image_description_markdown(image_data: dict, index: int = 1) -> str:
    """
    Format image description as Markdown section.

    Args:
        image_data: Dictionary with image info and description
        index: Image number for display

    Returns:
        str: Formatted Markdown string
    """
    page_num = image_data.get('page_num', '?')
    width = image_data.get('width', '?')
    height = image_data.get('height', '?')
    description = image_data.get('description', '[Sem descrição]')

    md = f"""### 🖼️ Imagem {index} (Página {page_num})

**Dimensões:** {width}x{height} pixels

{description}

---
"""

    return md
