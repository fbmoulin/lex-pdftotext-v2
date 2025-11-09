"""
Tests for configuration management system.

Tests config loading from YAML files, environment variables,
and the precedence hierarchy.
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest

from src.utils.config import Config, get_config, reload_config


class TestConfigDefaults:
    """Test default configuration values."""

    def test_config_default_values(self):
        """Test that Config initializes with correct defaults."""
        config = Config()

        # PDF Processing
        assert config.max_pdf_size_mb == 500
        assert config.max_pdf_pages == 10000
        assert config.pdf_open_timeout == 30

        # Text Processing
        assert config.chunk_size == 1000
        assert config.min_chunk_size == 100
        assert config.max_chunk_size == 10000

        # Image Processing
        assert config.max_image_size_mb == 4
        assert config.enable_image_analysis is False

        # API Configuration
        assert config.gemini_api_key is None
        assert config.gemini_rate_limit == 60

        # Output Configuration
        assert config.output_dir == "data/output"
        assert config.default_format == "markdown"

        # Logging
        assert config.log_level == "INFO"
        assert config.log_file == "logs/pdftotext.log"
        assert config.log_max_bytes == 10 * 1024 * 1024
        assert config.log_backup_count == 5

        # Disk Space
        assert config.min_disk_space_mb == 100

        # Validation
        assert config.validate_pdfs is True
        assert config.validate_output_paths is True

        # Performance
        assert config.batch_size == 10


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_chunk_size_validation_within_bounds(self):
        """Test that valid chunk_size is accepted."""
        config = Config(chunk_size=500, min_chunk_size=100, max_chunk_size=10000)
        assert config.chunk_size == 500

    def test_chunk_size_validation_below_min(self):
        """Test that chunk_size below min is adjusted."""
        config = Config(chunk_size=50, min_chunk_size=100, max_chunk_size=10000)
        assert config.chunk_size == 100

    def test_chunk_size_validation_above_max(self):
        """Test that chunk_size above max is adjusted."""
        config = Config(chunk_size=20000, min_chunk_size=100, max_chunk_size=10000)
        assert config.chunk_size == 10000

    def test_log_level_validation_valid(self):
        """Test that valid log levels are accepted."""
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            config = Config(log_level=level)
            assert config.log_level == level

    def test_log_level_validation_lowercase(self):
        """Test that lowercase log levels are uppercased."""
        config = Config(log_level='debug')
        assert config.log_level == 'DEBUG'

    def test_log_level_validation_invalid(self):
        """Test that invalid log level defaults to INFO."""
        config = Config(log_level='INVALID')
        assert config.log_level == 'INFO'


class TestConfigFromFile:
    """Test loading configuration from YAML files."""

    def test_load_from_valid_yaml(self, tmp_path):
        """Test loading configuration from valid YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'max_pdf_size_mb': 1000,
            'chunk_size': 2000,
            'log_level': 'DEBUG',
            'enable_image_analysis': True
        }

        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)

        config = Config.from_file(config_file)

        assert config.max_pdf_size_mb == 1000
        assert config.chunk_size == 2000
        assert config.log_level == 'DEBUG'
        assert config.enable_image_analysis is True

    def test_load_from_nonexistent_file(self, tmp_path):
        """Test loading from nonexistent file returns defaults."""
        config_file = tmp_path / "nonexistent.yaml"
        config = Config.from_file(config_file)

        # Should return default values
        assert config.max_pdf_size_mb == 500
        assert config.chunk_size == 1000

    def test_load_from_invalid_yaml(self, tmp_path):
        """Test loading from invalid YAML returns defaults."""
        config_file = tmp_path / "invalid.yaml"

        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [[[")

        config = Config.from_file(config_file)

        # Should return default values despite error
        assert config.max_pdf_size_mb == 500

    def test_load_from_empty_yaml(self, tmp_path):
        """Test loading from empty YAML file."""
        config_file = tmp_path / "empty.yaml"

        with open(config_file, 'w') as f:
            f.write("")

        config = Config.from_file(config_file)

        # Should return default values
        assert config.max_pdf_size_mb == 500


class TestConfigFromEnv:
    """Test loading configuration from environment variables."""

    def test_load_from_env_integers(self):
        """Test loading integer values from environment."""
        os.environ['MAX_PDF_SIZE_MB'] = '2000'
        os.environ['CHUNK_SIZE'] = '3000'
        os.environ['BATCH_SIZE'] = '50'

        config = Config.from_env()

        assert config.max_pdf_size_mb == 2000
        assert config.chunk_size == 3000
        assert config.batch_size == 50

        # Cleanup
        del os.environ['MAX_PDF_SIZE_MB']
        del os.environ['CHUNK_SIZE']
        del os.environ['BATCH_SIZE']

    def test_load_from_env_strings(self):
        """Test loading string values from environment."""
        os.environ['LOG_LEVEL'] = 'ERROR'
        os.environ['OUTPUT_DIR'] = 'custom/output'
        os.environ['GEMINI_API_KEY'] = 'test-api-key-123'

        config = Config.from_env()

        assert config.log_level == 'ERROR'
        assert config.output_dir == 'custom/output'
        assert config.gemini_api_key == 'test-api-key-123'

        # Cleanup
        del os.environ['LOG_LEVEL']
        del os.environ['OUTPUT_DIR']
        del os.environ['GEMINI_API_KEY']

    def test_load_from_env_booleans(self):
        """Test loading boolean values from environment."""
        os.environ['ENABLE_IMAGE_ANALYSIS'] = 'true'
        os.environ['VALIDATE_PDFS'] = 'false'

        config = Config.from_env()

        assert config.enable_image_analysis is True
        assert config.validate_pdfs is False

        # Cleanup
        del os.environ['ENABLE_IMAGE_ANALYSIS']
        del os.environ['VALIDATE_PDFS']

    def test_env_invalid_integer_uses_default(self):
        """Test that invalid integer env vars use defaults."""
        os.environ['CHUNK_SIZE'] = 'not-a-number'

        config = Config.from_env()

        # Should use default value
        assert config.chunk_size == 1000

        # Cleanup
        del os.environ['CHUNK_SIZE']

    def test_env_override_base_config(self):
        """Test that env vars override base config."""
        base_config = Config(chunk_size=500)
        os.environ['CHUNK_SIZE'] = '8000'

        config = Config.from_env(base_config)

        assert config.chunk_size == 8000

        # Cleanup
        del os.environ['CHUNK_SIZE']


class TestConfigPrecedence:
    """Test configuration precedence: env > yaml > defaults."""

    def test_precedence_env_over_yaml(self, tmp_path):
        """Test that environment variables override YAML config."""
        config_file = tmp_path / "config.yaml"
        config_data = {'chunk_size': 2000}

        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)

        # Set env var
        os.environ['CHUNK_SIZE'] = '5000'

        config = Config.load(config_file)

        # Env should win
        assert config.chunk_size == 5000

        # Cleanup
        del os.environ['CHUNK_SIZE']

    def test_precedence_yaml_over_defaults(self, tmp_path):
        """Test that YAML config overrides defaults."""
        config_file = tmp_path / "config.yaml"
        config_data = {'chunk_size': 3000}

        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)

        config = Config.load(config_file)

        # YAML should override default (1000)
        assert config.chunk_size == 3000

    def test_precedence_all_sources(self, tmp_path):
        """Test full precedence chain: env > yaml > default."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'chunk_size': 2000,      # From YAML
            'batch_size': 25,        # From YAML (no env override)
        }

        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)

        # Set env var for chunk_size only
        os.environ['CHUNK_SIZE'] = '7000'

        config = Config.load(config_file)

        # chunk_size from env (highest priority)
        assert config.chunk_size == 7000
        # batch_size from YAML (no env override)
        assert config.batch_size == 25
        # max_pdf_size_mb from default (not in YAML or env)
        assert config.max_pdf_size_mb == 500

        # Cleanup
        del os.environ['CHUNK_SIZE']


class TestConfigSave:
    """Test saving configuration to YAML file."""

    def test_save_config_to_file(self, tmp_path):
        """Test saving configuration to YAML file."""
        config_file = tmp_path / "saved_config.yaml"
        config = Config(chunk_size=5000, log_level='DEBUG')

        config.save(config_file)

        # Verify file was created
        assert config_file.exists()

        # Load and verify
        with open(config_file, 'r') as f:
            saved_data = yaml.safe_load(f)

        assert saved_data['chunk_size'] == 5000
        assert saved_data['log_level'] == 'DEBUG'

    def test_save_creates_directory(self, tmp_path):
        """Test that save creates parent directories."""
        config_file = tmp_path / "nested" / "dir" / "config.yaml"
        config = Config()

        config.save(config_file)

        assert config_file.exists()
        assert config_file.parent.exists()


class TestConfigToDict:
    """Test converting configuration to dictionary."""

    def test_to_dict_contains_all_fields(self):
        """Test that to_dict includes all configuration fields."""
        config = Config()
        config_dict = config.to_dict()

        # Check key fields are present
        assert 'max_pdf_size_mb' in config_dict
        assert 'chunk_size' in config_dict
        assert 'log_level' in config_dict
        assert 'enable_image_analysis' in config_dict

    def test_to_dict_matches_values(self):
        """Test that to_dict values match config attributes."""
        config = Config(chunk_size=3000, log_level='WARNING')
        config_dict = config.to_dict()

        assert config_dict['chunk_size'] == 3000
        assert config_dict['log_level'] == 'WARNING'


class TestGlobalConfig:
    """Test global configuration singleton."""

    def test_get_config_returns_instance(self):
        """Test that get_config returns a Config instance."""
        from src.utils.config import _config

        # Reset global config first
        import src.utils.config
        src.utils.config._config = None

        config = get_config()
        assert isinstance(config, Config)

    def test_reload_config_updates_global(self, tmp_path):
        """Test that reload_config updates global instance."""
        config_file = tmp_path / "reload.yaml"
        config_data = {'chunk_size': 9999}

        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)

        # Reset global config
        import src.utils.config
        src.utils.config._config = None

        # First load
        config1 = get_config()
        original_chunk = config1.chunk_size

        # Reload with new config
        config2 = reload_config(config_file)

        assert config2.chunk_size == 9999
        assert config2.chunk_size != original_chunk

    def test_get_config_singleton_behavior(self):
        """Test that get_config returns same instance."""
        # Reset global config
        import src.utils.config
        src.utils.config._config = None

        config1 = get_config()
        config2 = get_config()

        # Should be the same instance
        assert config1 is config2
