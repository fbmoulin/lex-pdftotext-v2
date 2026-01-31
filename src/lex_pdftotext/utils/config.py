"""
Configuration management for PDF Text Extractor.

Loads configuration from config.yaml and environment variables.
Environment variables take precedence over config file values.
"""

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .logger import get_logger

logger = get_logger(__name__)


def _get_base_path() -> Path:
    """Get base path for the application, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        # Running in normal Python environment - go up 2 levels from src/utils/
        return Path(__file__).parent.parent.parent


@dataclass
class Config:
    """Application configuration with defaults."""

    # PDF Processing
    max_pdf_size_mb: int = 500
    max_pdf_pages: int = 10000
    pdf_open_timeout: int = 30
    page_extraction_timeout: int = 10  # Timeout per page extraction

    # Text Processing
    chunk_size: int = 1000
    min_chunk_size: int = 100
    max_chunk_size: int = 10000

    # Image Processing
    max_image_size_mb: int = 4
    enable_image_analysis: bool = False

    # API Configuration
    gemini_api_key: str | None = None
    gemini_rate_limit: int = 60  # requests per minute
    gemini_api_timeout: int = 30  # API call timeout in seconds

    # Output Configuration
    output_dir: str = "data/output"
    default_format: str = "markdown"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/pdftotext.log"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Disk Space
    min_disk_space_mb: int = 100  # Minimum free space required

    # Validation
    validate_pdfs: bool = True
    validate_output_paths: bool = True

    # Performance
    batch_size: int = 10  # Number of PDFs to process before showing progress

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate chunk size
        if not (self.min_chunk_size <= self.chunk_size <= self.max_chunk_size):
            logger.warning(
                f"chunk_size {self.chunk_size} out of bounds, setting to {self.min_chunk_size}"
            )
            self.chunk_size = max(self.min_chunk_size, min(self.chunk_size, self.max_chunk_size))

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            logger.warning(f"Invalid log level '{self.log_level}', using INFO")
            self.log_level = "INFO"
        else:
            self.log_level = self.log_level.upper()

        logger.debug(f"Configuration initialized: {self}")

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml file

        Returns:
            Config instance
        """
        if not config_path.exists():
            logger.info(f"Config file not found: {config_path}, using defaults")
            return cls()

        try:
            with open(config_path, encoding="utf-8") as f:
                config_dict = yaml.safe_load(f) or {}

            logger.info(f"Loaded configuration from: {config_path}")
            return cls(**config_dict)

        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file {config_path}: {e}")
            logger.warning("Using default configuration")
            return cls()

        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            logger.warning("Using default configuration")
            return cls()

    @classmethod
    def from_env(cls, base_config: Optional["Config"] = None) -> "Config":
        """
        Load configuration from environment variables.

        Environment variables override file configuration.

        Args:
            base_config: Base configuration to override (optional)

        Returns:
            Config instance
        """
        if base_config is None:
            base_config = cls()

        # Create dict from base config
        config_dict = base_config.__dict__.copy()

        # Override with environment variables
        env_mappings: dict[str, tuple[str, Callable[[str], Any]]] = {
            "MAX_PDF_SIZE_MB": ("max_pdf_size_mb", int),
            "MAX_PDF_PAGES": ("max_pdf_pages", int),
            "PDF_OPEN_TIMEOUT": ("pdf_open_timeout", int),
            "PAGE_EXTRACTION_TIMEOUT": ("page_extraction_timeout", int),
            "CHUNK_SIZE": ("chunk_size", int),
            "MIN_CHUNK_SIZE": ("min_chunk_size", int),
            "MAX_CHUNK_SIZE": ("max_chunk_size", int),
            "MAX_IMAGE_SIZE_MB": ("max_image_size_mb", int),
            "ENABLE_IMAGE_ANALYSIS": ("enable_image_analysis", lambda x: x.lower() == "true"),
            "GEMINI_API_KEY": ("gemini_api_key", str),
            "GEMINI_RATE_LIMIT": ("gemini_rate_limit", int),
            "GEMINI_API_TIMEOUT": ("gemini_api_timeout", int),
            "OUTPUT_DIR": ("output_dir", str),
            "DEFAULT_FORMAT": ("default_format", str),
            "LOG_LEVEL": ("log_level", str),
            "LOG_FILE": ("log_file", str),
            "LOG_MAX_BYTES": ("log_max_bytes", int),
            "LOG_BACKUP_COUNT": ("log_backup_count", int),
            "MIN_DISK_SPACE_MB": ("min_disk_space_mb", int),
            "VALIDATE_PDFS": ("validate_pdfs", lambda x: x.lower() == "true"),
            "VALIDATE_OUTPUT_PATHS": ("validate_output_paths", lambda x: x.lower() == "true"),
            "BATCH_SIZE": ("batch_size", int),
        }

        for env_var, (config_key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    config_dict[config_key] = converter(value)
                    logger.debug(
                        f"Config overridden from env: {config_key} = {config_dict[config_key]}"
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid value for {env_var}='{value}': {e}. "
                        f"Using default: {config_dict[config_key]}"
                    )

        return cls(**config_dict)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        """
        Load configuration from file and environment.

        Priority: Environment variables > config.yaml > defaults

        Args:
            config_path: Path to config file (default: ./config.yaml)

        Returns:
            Config instance
        """
        if config_path is None:
            # Use PyInstaller-aware path resolution
            config_path = _get_base_path() / "config.yaml"

        # Load from file first
        file_config = cls.from_file(config_path)

        # Override with environment variables
        final_config = cls.from_env(file_config)

        logger.info("Configuration loaded successfully")
        return final_config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return self.__dict__.copy()

    def save(self, config_path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            config_path: Path to save config.yaml
        """
        try:
            # Create directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict and remove None values
            config_dict = {k: v for k, v in self.to_dict().items() if v is not None}

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Configuration saved to: {config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """
    Get global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config(config_path: Path | None = None) -> Config:
    """
    Reload configuration from file and environment.

    Args:
        config_path: Path to config file (optional)

    Returns:
        Reloaded Config instance
    """
    global _config
    _config = Config.load(config_path)
    return _config
