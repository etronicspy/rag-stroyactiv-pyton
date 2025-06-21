"""
🧪 Unit Tests for Logging Configuration

Test suite for the logging configuration system covering:
- LoggingSettings validation
- ConfigurationValidator functionality
- ConfigurationProvider access
- Environment variable parsing

Author: AI Assistant
Created: 2024
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from core.logging.config.settings import LoggingSettings, get_logging_settings, LogLevel
from core.logging.config.validator import ConfigurationValidator, validate_configuration
from core.logging.config.provider import ConfigurationProvider, get_configuration


class TestLoggingSettings:
    """Tests for LoggingSettings class"""
    
    def test_default_settings_creation(self):
        """Test that default settings can be created without errors."""
        settings = LoggingSettings()
        assert settings is not None
        assert settings.GENERAL.DEFAULT_LEVEL == LogLevel.INFO
        assert settings.FORMATTER.DEFAULT_TYPE.value == "text"
        assert settings.HANDLER.DEFAULT_TYPES[0].value == "console"
    
    def test_settings_from_env(self):
        """Test creating settings from environment variables."""
        with patch.dict(os.environ, {
            "LOG_GENERAL_DEFAULT_LEVEL": "DEBUG",
            "LOG_FORMATTER_ENABLE_COLORS": "true",
            "LOG_HANDLER_FILE_PATH": "/tmp/test.log"
        }):
            settings = LoggingSettings.from_env()
            assert settings.GENERAL.DEFAULT_LEVEL == LogLevel.DEBUG
            assert settings.FORMATTER.ENABLE_COLORS is True
            assert settings.HANDLER.FILE_PATH == "/tmp/test.log"
    
    def test_type_conversion(self):
        """Test proper type conversion of environment variables."""
        with patch.dict(os.environ, {
            "LOG_GENERAL_WORKER_COUNT": "5",
            "LOG_GENERAL_FLUSH_INTERVAL": "0.75",
            "LOG_MEMORY_ENABLE_LOGGER_POOL": "true",
            "LOG_HTTP_MAX_BODY_SIZE": "20480"
        }):
            settings = LoggingSettings.from_env()
            assert settings.GENERAL.WORKER_COUNT == 5
            assert settings.GENERAL.FLUSH_INTERVAL == 0.75
            assert settings.MEMORY.ENABLE_LOGGER_POOL is True
            assert settings.HTTP.MAX_BODY_SIZE == 20480
    
    def test_validators(self):
        """Test field validators for LoggingSettings."""
        settings = LoggingSettings(
            GENERAL={
                "WORKER_COUNT": 0,  # Should be corrected to 1
                "FLUSH_INTERVAL": 0.05,  # Should be corrected to 0.1
                "BATCH_SIZE": 0,  # Should be corrected to 1
                "QUEUE_SIZE": 5  # Should be corrected to 10
            }
        )
        
        assert settings.GENERAL.WORKER_COUNT == 1
        assert settings.GENERAL.FLUSH_INTERVAL == 0.1
        assert settings.GENERAL.BATCH_SIZE == 1
        assert settings.GENERAL.QUEUE_SIZE == 10


class TestConfigurationValidator:
    """Tests for ConfigurationValidator class"""
    
    def test_valid_configuration(self):
        """Test validation of valid configuration."""
        settings = LoggingSettings()
        validator = ConfigurationValidator(settings)
        
        assert validator.validate() is True
        assert len(validator.get_errors()) == 0
    
    def test_invalid_log_level(self):
        """Test validation of invalid log level."""
        settings = LoggingSettings()
        settings.GENERAL.DEFAULT_LEVEL = "INVALID_LEVEL"  # type: ignore
        
        validator = ConfigurationValidator(settings)
        assert validator.validate() is False
        assert len(validator.get_errors()) > 0
        assert any("log level" in error.lower() for error in validator.get_errors())
    
    def test_invalid_handler_settings(self):
        """Test validation of invalid handler settings."""
        settings = LoggingSettings()
        settings.HANDLER.CONSOLE_STREAM = "invalid_stream"  # Should be stdout or stderr
        settings.HANDLER.ROTATING_FILE_MAX_BYTES = 500  # Should be at least 1024
        
        validator = ConfigurationValidator(settings)
        assert validator.validate() is False
        assert len(validator.get_errors()) >= 2
    
    def test_warnings_for_missing_directories(self):
        """Test warnings for missing log directories."""
        settings = LoggingSettings()
        settings.HANDLER.FILE_PATH = "/non/existent/directory/test.log"
        
        validator = ConfigurationValidator(settings)
        validator.validate()
        
        assert len(validator.get_warnings()) > 0
        assert any("directory does not exist" in warning.lower() for warning in validator.get_warnings())
    
    def test_validate_configuration_function(self):
        """Test the validate_configuration function."""
        with patch('core.logging.config.validator.get_logging_settings') as mock_get_settings:
            mock_get_settings.return_value = LoggingSettings()
            validator = validate_configuration()
            
            assert validator is not None
            assert isinstance(validator, ConfigurationValidator)
            assert validator.validate() is True


class TestConfigurationProvider:
    """Tests for ConfigurationProvider class"""
    
    def test_get_configuration(self):
        """Test getting configuration provider singleton."""
        with patch('core.logging.config.provider.get_logging_settings') as mock_get_settings:
            mock_get_settings.return_value = LoggingSettings()
            
            config = get_configuration()
            assert config is not None
            assert isinstance(config, ConfigurationProvider)
            
            # Second call should return the same instance
            config2 = get_configuration()
            assert config is config2
    
    def test_get_log_level(self):
        """Test getting log level for different loggers."""
        settings = LoggingSettings(
            GENERAL={
                "DEFAULT_LEVEL": LogLevel.INFO,
                "THIRD_PARTY_LEVEL": LogLevel.WARNING
            }
        )
        
        provider = ConfigurationProvider(settings)
        
        # Core module should get default level
        assert provider.get_log_level("core.logging") == logging.INFO
        
        # Third-party module should get third-party level
        assert provider.get_log_level("requests") == logging.WARNING
    
    def test_get_settings_methods(self):
        """Test methods that get specific settings sections."""
        settings = LoggingSettings()
        provider = ConfigurationProvider(settings)
        
        formatter_settings = provider.get_formatter_settings()
        assert formatter_settings is not None
        assert "type" in formatter_settings
        assert formatter_settings["type"] == settings.FORMATTER.DEFAULT_TYPE.value
        
        handler_settings = provider.get_handler_settings()
        assert handler_settings is not None
        assert "types" in handler_settings
        assert handler_settings["types"] == [h.value for h in settings.HANDLER.DEFAULT_TYPES]
        
        context_settings = provider.get_context_settings()
        assert context_settings is not None
        assert "enable_correlation_id" in context_settings
        assert context_settings["enable_correlation_id"] == settings.CONTEXT.ENABLE_CORRELATION_ID
    
    def test_get_value(self):
        """Test getting individual configuration values."""
        settings = LoggingSettings()
        provider = ConfigurationProvider(settings)
        
        # Test getting existing value
        value = provider.get_value("GENERAL.DEFAULT_LEVEL")
        assert value == settings.GENERAL.DEFAULT_LEVEL
        
        # Test getting non-existent section
        value = provider.get_value("NON_EXISTENT.OPTION", "default")
        assert value == "default"
        
        # Test getting non-existent option
        value = provider.get_value("GENERAL.NON_EXISTENT", 42)
        assert value == 42
        
        # Test invalid path format
        with pytest.raises(ValueError):
            provider.get_value("INVALID_PATH_FORMAT")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 