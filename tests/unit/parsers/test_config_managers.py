"""
Unit Tests for Parser Configuration Managers

Tests for configuration management in core.parsers.config
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import json
import os

from core.parsers.config import (
    ParserConfigManager,
    get_config_manager,
    SystemPromptsManager,
    get_system_prompts_manager,
    UnitsConfigManager,
    get_units_config_manager
)


class TestParserConfigManager:
    """Tests for ParserConfigManager"""
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization"""
        config_manager = ParserConfigManager()
        
        assert config_manager.current_profile == "default"
        assert hasattr(config_manager, 'profiles')
        assert hasattr(config_manager, 'config_file')
        assert hasattr(config_manager, 'logger')
    
    def test_get_config_manager_singleton(self):
        """Test singleton pattern for config manager"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, ParserConfigManager)
    
    def test_available_profiles(self):
        """Test available configuration profiles"""
        config_manager = ParserConfigManager()
        profiles = config_manager.get_available_profiles()
        
        assert isinstance(profiles, list)
        assert len(profiles) > 0
        assert "default" in profiles
        assert "development" in profiles
        assert "production" in profiles
        assert "testing" in profiles
    
    def test_switch_profile_valid(self):
        """Test switching to valid profile"""
        config_manager = ParserConfigManager()
        
        # Test switching to development profile
        result = config_manager.switch_profile("development")
        assert result is True
        assert config_manager.current_profile == "development"
        
        # Test switching back to default
        result = config_manager.switch_profile("default")
        assert result is True
        assert config_manager.current_profile == "default"
    
    def test_switch_profile_invalid(self):
        """Test switching to invalid profile"""
        config_manager = ParserConfigManager()
        
        result = config_manager.switch_profile("invalid_profile")
        assert result is False
        assert config_manager.current_profile == "default"  # Should remain unchanged
    
    def test_get_current_config(self):
        """Test getting current configuration"""
        config_manager = ParserConfigManager()
        
        config = config_manager.get_current_config()
        assert isinstance(config, dict)
        assert "openai_model" in config
        assert "timeout" in config
        assert "max_retries" in config
        assert "enable_embeddings" in config
    
    def test_get_profile_config(self):
        """Test getting specific profile configuration"""
        config_manager = ParserConfigManager()
        
        # Test default profile
        default_config = config_manager.get_profile_config("default")
        assert isinstance(default_config, dict)
        assert "openai_model" in default_config
        
        # Test development profile
        dev_config = config_manager.get_profile_config("development")
        assert isinstance(dev_config, dict)
        assert "openai_model" in dev_config
        
        # Test production profile
        prod_config = config_manager.get_profile_config("production")
        assert isinstance(prod_config, dict)
        assert "openai_model" in prod_config
    
    def test_get_profile_config_invalid(self):
        """Test getting invalid profile configuration"""
        config_manager = ParserConfigManager()
        
        config = config_manager.get_profile_config("invalid_profile")
        assert config is None
    
    def test_update_profile_config(self):
        """Test updating profile configuration"""
        config_manager = ParserConfigManager()
        
        # Update some configuration values
        updates = {
            "openai_model": "gpt-4",
            "timeout": 60,
            "enable_debug": True
        }
        
        result = config_manager.update_profile_config("default", updates)
        assert result is True
        
        # Verify updates were applied
        updated_config = config_manager.get_profile_config("default")
        assert updated_config["openai_model"] == "gpt-4"
        assert updated_config["timeout"] == 60
        assert updated_config["enable_debug"] is True
    
    def test_update_profile_config_invalid_profile(self):
        """Test updating invalid profile configuration"""
        config_manager = ParserConfigManager()
        
        updates = {"openai_model": "gpt-4"}
        result = config_manager.update_profile_config("invalid_profile", updates)
        assert result is False
    
    def test_reset_profile_config(self):
        """Test resetting profile configuration"""
        config_manager = ParserConfigManager()
        
        # First update the config
        updates = {"openai_model": "gpt-4", "timeout": 60}
        config_manager.update_profile_config("default", updates)
        
        # Then reset it
        result = config_manager.reset_profile_config("default")
        assert result is True
        
        # Verify reset worked
        reset_config = config_manager.get_profile_config("default")
        assert reset_config["openai_model"] != "gpt-4"  # Should be back to default
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config"""
        config_manager = ParserConfigManager()
        
        valid_config = {
            "openai_model": "gpt-4o-mini",
            "timeout": 30,
            "max_retries": 3,
            "enable_embeddings": True
        }
        
        is_valid, errors = config_manager.validate_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config"""
        config_manager = ParserConfigManager()
        
        invalid_config = {
            "openai_model": "",  # Empty model
            "timeout": -5,  # Negative timeout
            "max_retries": "invalid",  # Wrong type
            "enable_embeddings": "yes"  # Wrong type
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_export_config(self):
        """Test exporting configuration"""
        config_manager = ParserConfigManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Export configuration
            result = config_manager.export_config(temp_path)
            assert result is True
            
            # Verify file exists and contains valid JSON
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            
            assert isinstance(exported_data, dict)
            assert "profiles" in exported_data
            assert "metadata" in exported_data
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_import_config(self):
        """Test importing configuration"""
        config_manager = ParserConfigManager()
        
        # Create test configuration file
        test_config = {
            "profiles": {
                "test_profile": {
                    "openai_model": "gpt-4",
                    "timeout": 45,
                    "max_retries": 5
                }
            },
            "metadata": {
                "version": "1.0.0",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            # Import configuration
            result = config_manager.import_config(temp_path)
            assert result is True
            
            # Verify imported profile is available
            profiles = config_manager.get_available_profiles()
            assert "test_profile" in profiles
            
            # Verify imported config values
            imported_config = config_manager.get_profile_config("test_profile")
            assert imported_config["openai_model"] == "gpt-4"
            assert imported_config["timeout"] == 45
            assert imported_config["max_retries"] == 5
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_statistics(self):
        """Test getting configuration statistics"""
        config_manager = ParserConfigManager()
        
        stats = config_manager.get_statistics()
        assert isinstance(stats, dict)
        assert "total_profiles" in stats
        assert "current_profile" in stats
        assert "config_updates" in stats
        assert "last_updated" in stats
    
    def test_add_change_callback(self):
        """Test adding configuration change callback"""
        config_manager = ParserConfigManager()
        
        callback_called = False
        callback_profile = None
        callback_changes = None
        
        def test_callback(profile: str, changes: Dict[str, Any]):
            nonlocal callback_called, callback_profile, callback_changes
            callback_called = True
            callback_profile = profile
            callback_changes = changes
        
        # Add callback
        config_manager.add_change_callback(test_callback)
        
        # Make a change
        updates = {"openai_model": "gpt-4"}
        config_manager.update_profile_config("default", updates)
        
        # Verify callback was called
        assert callback_called is True
        assert callback_profile == "default"
        assert callback_changes == updates


class TestSystemPromptsManager:
    """Tests for SystemPromptsManager"""
    
    def test_prompts_manager_initialization(self):
        """Test system prompts manager initialization"""
        prompts_manager = SystemPromptsManager()
        
        assert hasattr(prompts_manager, 'prompts')
        assert hasattr(prompts_manager, 'templates')
        assert hasattr(prompts_manager, 'logger')
    
    def test_get_system_prompts_manager_singleton(self):
        """Test singleton pattern for system prompts manager"""
        manager1 = get_system_prompts_manager()
        manager2 = get_system_prompts_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, SystemPromptsManager)
    
    def test_get_available_prompts(self):
        """Test getting available prompts"""
        prompts_manager = SystemPromptsManager()
        
        prompts = prompts_manager.get_available_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        assert "main_parsing_prompt" in prompts
        assert "color_extraction_prompt" in prompts
        assert "unit_parsing_prompt" in prompts
    
    def test_get_prompt_valid(self):
        """Test getting valid prompt"""
        prompts_manager = SystemPromptsManager()
        
        prompt = prompts_manager.get_prompt("main_parsing_prompt")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_get_prompt_invalid(self):
        """Test getting invalid prompt"""
        prompts_manager = SystemPromptsManager()
        
        prompt = prompts_manager.get_prompt("invalid_prompt")
        assert prompt is None
    
    def test_get_prompt_with_variables(self):
        """Test getting prompt with variable substitution"""
        prompts_manager = SystemPromptsManager()
        
        variables = {
            "material_name": "кирпич красный",
            "material_unit": "шт",
            "material_price": "25.0"
        }
        
        prompt = prompts_manager.get_prompt("main_parsing_prompt", variables)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Variables should be substituted
        assert "кирпич красный" in prompt
    
    def test_update_prompt(self):
        """Test updating prompt"""
        prompts_manager = SystemPromptsManager()
        
        new_prompt = "Test prompt for {material_name}"
        result = prompts_manager.update_prompt("test_prompt", new_prompt)
        assert result is True
        
        # Verify update
        updated_prompt = prompts_manager.get_prompt("test_prompt")
        assert updated_prompt == new_prompt
    
    def test_get_prompt_template(self):
        """Test getting prompt template"""
        prompts_manager = SystemPromptsManager()
        
        template = prompts_manager.get_prompt_template("main_parsing_prompt")
        assert isinstance(template, dict)
        assert "template" in template
        assert "variables" in template
        assert "description" in template
    
    def test_list_prompt_variables(self):
        """Test listing prompt variables"""
        prompts_manager = SystemPromptsManager()
        
        variables = prompts_manager.list_prompt_variables("main_parsing_prompt")
        assert isinstance(variables, list)
        assert len(variables) > 0
    
    def test_validate_prompt_variables(self):
        """Test validating prompt variables"""
        prompts_manager = SystemPromptsManager()
        
        # Valid variables
        valid_vars = {"material_name": "кирпич", "material_unit": "шт"}
        is_valid, missing = prompts_manager.validate_prompt_variables("main_parsing_prompt", valid_vars)
        assert is_valid is True
        assert len(missing) == 0
        
        # Invalid variables (missing required)
        invalid_vars = {"material_name": "кирпич"}
        is_valid, missing = prompts_manager.validate_prompt_variables("main_parsing_prompt", invalid_vars)
        assert is_valid is False
        assert len(missing) > 0
    
    def test_get_statistics(self):
        """Test getting prompts statistics"""
        prompts_manager = SystemPromptsManager()
        
        stats = prompts_manager.get_statistics()
        assert isinstance(stats, dict)
        assert "total_prompts" in stats
        assert "total_templates" in stats
        assert "prompt_usage" in stats
        assert "last_updated" in stats


class TestUnitsConfigManager:
    """Tests for UnitsConfigManager"""
    
    def test_units_manager_initialization(self):
        """Test units config manager initialization"""
        units_manager = UnitsConfigManager()
        
        assert hasattr(units_manager, 'units')
        assert hasattr(units_manager, 'conversions')
        assert hasattr(units_manager, 'logger')
    
    def test_get_units_config_manager_singleton(self):
        """Test singleton pattern for units config manager"""
        manager1 = get_units_config_manager()
        manager2 = get_units_config_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, UnitsConfigManager)
    
    def test_get_available_units(self):
        """Test getting available units"""
        units_manager = UnitsConfigManager()
        
        units = units_manager.get_available_units()
        assert isinstance(units, list)
        assert len(units) > 0
        assert "шт" in units
        assert "м" in units
        assert "кг" in units
        assert "м2" in units
        assert "м3" in units
    
    def test_get_unit_info(self):
        """Test getting unit information"""
        units_manager = UnitsConfigManager()
        
        info = units_manager.get_unit_info("м")
        assert isinstance(info, dict)
        assert "name" in info
        assert "type" in info
        assert "base_unit" in info
        assert "conversion_factor" in info
    
    def test_get_unit_info_invalid(self):
        """Test getting invalid unit information"""
        units_manager = UnitsConfigManager()
        
        info = units_manager.get_unit_info("invalid_unit")
        assert info is None
    
    def test_normalize_unit(self):
        """Test unit normalization"""
        units_manager = UnitsConfigManager()
        
        # Test various unit normalizations
        assert units_manager.normalize_unit("штука") == "шт"
        assert units_manager.normalize_unit("штук") == "шт"
        assert units_manager.normalize_unit("метр") == "м"
        assert units_manager.normalize_unit("килограмм") == "кг"
        assert units_manager.normalize_unit("квадратный метр") == "м2"
        assert units_manager.normalize_unit("кубический метр") == "м3"
    
    def test_normalize_unit_invalid(self):
        """Test normalizing invalid unit"""
        units_manager = UnitsConfigManager()
        
        normalized = units_manager.normalize_unit("invalid_unit")
        assert normalized is None
    
    def test_get_conversion_factor(self):
        """Test getting conversion factor"""
        units_manager = UnitsConfigManager()
        
        # Test conversion from derived units to base units
        factor = units_manager.get_conversion_factor("см", "м")
        assert factor == 0.01
        
        factor = units_manager.get_conversion_factor("г", "кг")
        assert factor == 0.001
        
        factor = units_manager.get_conversion_factor("мм", "м")
        assert factor == 0.001
    
    def test_get_conversion_factor_invalid(self):
        """Test getting conversion factor for invalid units"""
        units_manager = UnitsConfigManager()
        
        factor = units_manager.get_conversion_factor("invalid_unit", "м")
        assert factor is None
        
        factor = units_manager.get_conversion_factor("м", "invalid_unit")
        assert factor is None
    
    def test_convert_unit(self):
        """Test unit conversion"""
        units_manager = UnitsConfigManager()
        
        # Test various conversions
        result = units_manager.convert_unit(100, "см", "м")
        assert result == 1.0
        
        result = units_manager.convert_unit(1000, "г", "кг")
        assert result == 1.0
        
        result = units_manager.convert_unit(1000, "мм", "м")
        assert result == 1.0
    
    def test_convert_unit_invalid(self):
        """Test converting with invalid units"""
        units_manager = UnitsConfigManager()
        
        result = units_manager.convert_unit(100, "invalid_unit", "м")
        assert result is None
        
        result = units_manager.convert_unit(100, "см", "invalid_unit")
        assert result is None
    
    def test_get_unit_suggestions(self):
        """Test getting unit suggestions"""
        units_manager = UnitsConfigManager()
        
        suggestions = units_manager.get_unit_suggestions("шту")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert "шт" in suggestions
        
        suggestions = units_manager.get_unit_suggestions("килог")
        assert isinstance(suggestions, list)
        assert "кг" in suggestions
    
    def test_validate_unit(self):
        """Test unit validation"""
        units_manager = UnitsConfigManager()
        
        # Valid units
        assert units_manager.validate_unit("шт") is True
        assert units_manager.validate_unit("м") is True
        assert units_manager.validate_unit("кг") is True
        
        # Invalid units
        assert units_manager.validate_unit("invalid_unit") is False
        assert units_manager.validate_unit("") is False
        assert units_manager.validate_unit(None) is False
    
    def test_get_units_by_type(self):
        """Test getting units by type"""
        units_manager = UnitsConfigManager()
        
        # Test different unit types
        length_units = units_manager.get_units_by_type("length")
        assert isinstance(length_units, list)
        assert "м" in length_units
        assert "см" in length_units
        assert "мм" in length_units
        
        weight_units = units_manager.get_units_by_type("weight")
        assert isinstance(weight_units, list)
        assert "кг" in weight_units
        assert "г" in weight_units
        
        count_units = units_manager.get_units_by_type("count")
        assert isinstance(count_units, list)
        assert "шт" in count_units
    
    def test_get_units_by_type_invalid(self):
        """Test getting units by invalid type"""
        units_manager = UnitsConfigManager()
        
        units = units_manager.get_units_by_type("invalid_type")
        assert units == []
    
    def test_get_statistics(self):
        """Test getting units statistics"""
        units_manager = UnitsConfigManager()
        
        stats = units_manager.get_statistics()
        assert isinstance(stats, dict)
        assert "total_units" in stats
        assert "units_by_type" in stats
        assert "conversion_pairs" in stats
        assert "normalization_rules" in stats


class TestConfigManagerIntegration:
    """Integration tests for configuration managers"""
    
    def test_config_managers_work_together(self):
        """Test that all config managers work together"""
        # Get all managers
        config_manager = get_config_manager()
        prompts_manager = get_system_prompts_manager()
        units_manager = get_units_config_manager()
        
        # Verify they're all initialized
        assert config_manager is not None
        assert prompts_manager is not None
        assert units_manager is not None
        
        # Test basic functionality
        assert len(config_manager.get_available_profiles()) > 0
        assert len(prompts_manager.get_available_prompts()) > 0
        assert len(units_manager.get_available_units()) > 0
    
    def test_config_managers_statistics(self):
        """Test that all config managers provide statistics"""
        config_manager = get_config_manager()
        prompts_manager = get_system_prompts_manager()
        units_manager = get_units_config_manager()
        
        # Get statistics from all managers
        config_stats = config_manager.get_statistics()
        prompts_stats = prompts_manager.get_statistics()
        units_stats = units_manager.get_statistics()
        
        # Verify statistics are valid
        assert isinstance(config_stats, dict)
        assert isinstance(prompts_stats, dict)
        assert isinstance(units_stats, dict)
        
        # Verify they have required keys
        assert "total_profiles" in config_stats
        assert "total_prompts" in prompts_stats
        assert "total_units" in units_stats


if __name__ == "__main__":
    pytest.main([__file__]) 