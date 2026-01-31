"""Image analysis using Google Gemini API."""

import io
import os

from PIL import Image
from ratelimit import limits, sleep_and_retry
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..utils.cache import ImageDescriptionCache, get_image_cache
from ..utils.config import get_config
from ..utils.logger import get_logger

# Initialize logger and config
logger = get_logger(__name__)
config = get_config()


class ImageAnalyzer:
    """
    Analyze images using Google Gemini Vision API.

    Generates contextual descriptions of images found in legal documents,
    identifying evidence, exhibits, signatures, stamps, etc.
    """

    def __init__(
        self, api_key: str | None = None, max_image_size_mb: int = 4, enable_cache: bool = True
    ):
        """
        Initialize image analyzer with Gemini API.

        Args:
            api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
            max_image_size_mb: Maximum image size in MB before resizing (default: 4MB)
            enable_cache: Enable caching of image descriptions (default: True)

        Raises:
            ValueError: If no API key is found
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.max_image_size_mb = max_image_size_mb
        self.enable_cache = enable_cache
        self.cache: ImageDescriptionCache | None

        # Initialize cache if enabled
        if self.enable_cache:
            self.cache = get_image_cache()
            logger.info("Image description caching enabled")
        else:
            self.cache = None
            logger.info("Image description caching disabled")

        if not self.api_key:
            logger.error("Gemini API key not found in environment")
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Lazy import to avoid requiring google-generativeai if not using images
        try:
            import google.generativeai as genai

            self.genai = genai
            self.genai.configure(api_key=self.api_key)
            self.model = self.genai.GenerativeModel("gemini-1.5-flash")
            logger.info("ImageAnalyzer initialized with Gemini API")
        except ImportError as e:
            logger.error(f"Failed to import google-generativeai: {e}")
            raise ImportError(
                "google-generativeai not installed. Install with: pip install google-generativeai"
            ) from e

    def _resize_image_if_needed(self, image: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum size.

        Args:
            image: PIL Image to check and resize

        Returns:
            Original or resized PIL Image
        """
        # Calculate current size
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        size_mb = len(img_buffer.getvalue()) / (1024 * 1024)

        if size_mb > self.max_image_size_mb:
            logger.warning(
                f"Image size {size_mb:.2f}MB exceeds {self.max_image_size_mb}MB, resizing..."
            )

            # Calculate new dimensions (reduce by half iteratively until under limit)
            width, height = image.size
            while size_mb > self.max_image_size_mb:
                width = int(width * 0.7)
                height = int(height * 0.7)

                resized = image.resize((width, height), Image.Resampling.LANCZOS)

                # Recalculate size
                img_buffer = io.BytesIO()
                resized.save(img_buffer, format="PNG")
                size_mb = len(img_buffer.getvalue()) / (1024 * 1024)

            logger.info(f"Image resized to {width}x{height} ({size_mb:.2f}MB)")
            return resized

        return image

    @sleep_and_retry
    @limits(calls=60, period=60)  # 60 calls per minute
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def _call_gemini_api(self, prompt: str, image: Image.Image) -> str:
        """
        Call Gemini API with retry and rate limiting.

        Args:
            prompt: Text prompt for analysis
            image: PIL Image to analyze

        Returns:
            API response text

        Raises:
            Exception: If all retries fail
        """
        try:
            logger.debug(
                f"Calling Gemini API for image analysis (timeout: {config.gemini_api_timeout}s)"
            )
            response = self.model.generate_content(
                [prompt, image], request_options={"timeout": config.gemini_api_timeout}
            )

            if not response or not response.text:
                logger.warning("Empty response from Gemini API")
                raise ValueError("Empty response from Gemini API")

            logger.debug("Successfully received Gemini API response")
            return str(response.text.strip())

        except Exception as e:
            logger.error(f"Gemini API call failed: {type(e).__name__}: {str(e)}")
            raise

    def describe_image(
        self, image: Image.Image, context: str = "legal document", page_num: int | None = None
    ) -> str:
        """
        Generate a description of an image using Gemini Vision.

        Checks cache first to avoid redundant API calls for identical images.

        Args:
            image: PIL Image object to analyze
            context: Context about the document (e.g., "legal petition", "court decision")
            page_num: Page number where image appears (optional)

        Returns:
            str: Description of the image in Portuguese

        Raises:
            Exception: If image analysis fails after all retries
        """
        logger.info(f"Analyzing image from page {page_num or 'unknown'}")

        # Check cache first if enabled
        if self.cache:
            cached_description = self.cache.get(image, context)
            if cached_description:
                logger.info("Using cached image description (API call saved)")
                return cached_description

        # Build prompt
        prompt = self._build_prompt(context, page_num)

        try:
            # Resize image if needed
            processed_image = self._resize_image_if_needed(image)

            # Call API with retry and rate limiting
            description = self._call_gemini_api(prompt, processed_image)

            # Cache the result if caching is enabled
            if self.cache:
                self.cache.set(image, description, context)

            logger.info("Image analysis completed successfully")
            return str(description)

        except Exception as e:
            logger.error(f"Failed to analyze image: {type(e).__name__}: {str(e)}", exc_info=True)
            raise  # Raise exception instead of returning error string

    def describe_images_batch(
        self, images: list[dict], context: str = "legal document"
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
        total = len(images)

        logger.info(f"Starting batch image analysis for {total} images")

        for idx, img_data in enumerate(images, 1):
            try:
                logger.debug(f"Processing image {idx}/{total}")

                description = self.describe_image(
                    img_data["image"], context=context, page_num=img_data["page_num"]
                )

                # Add description to image data
                img_data_copy = img_data.copy()
                img_data_copy["description"] = description
                results.append(img_data_copy)

            except Exception as e:
                # Log error but continue processing other images
                logger.warning(
                    f"Failed to analyze image {idx}/{total} from page {img_data.get('page_num')}: "
                    f"{type(e).__name__}: {str(e)}"
                )

                # Add error as description
                img_data_copy = img_data.copy()
                img_data_copy["description"] = f"[Erro: {type(e).__name__}]"
                results.append(img_data_copy)

        logger.info(f"Batch image analysis completed: {len(results)} images processed")
        return results

    def _build_prompt(self, context: str, page_num: int | None = None) -> str:
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
    page_num = image_data.get("page_num", "?")
    width = image_data.get("width", "?")
    height = image_data.get("height", "?")
    description = image_data.get("description", "[Sem descrição]")

    md = f"""### 🖼️ Imagem {index} (Página {page_num})

**Dimensões:** {width}x{height} pixels

{description}

---
"""

    return md
