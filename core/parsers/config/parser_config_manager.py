"""
Parser Configuration Manager

Advanced configuration management for parser operations with environment integration,
validation, and dynamic configuration updates.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Core infrastructure imports
from core.config.parsers import ParserConfig, get_parser_config
from core.config.parsers import ParserConstants
from core.logging import get_logger


@dataclass
class ParserConfigProfile:
    """Parser configuration profile for different environments"""
    name: str
    description: str
    config: ParserConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "config": asdict(self.config)
        }


class ParserConfigManager:
    """
    Advanced configuration manager for parser operations.
    
    Provides centralized configuration management with environment-specific profiles,
    validation, dynamic updates, and comprehensive configuration export/import.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize Parser Configuration Manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.logger = get_logger(__name__)
        
        # Current configuration
        self._current_config = get_parser_config()
        self._current_profile = "default"
        
        # Configuration profiles
        self._profiles: Dict[str, ParserConfigProfile] = {}
        
        # Configuration change callbacks
        self._change_callbacks: List[callable] = []
        
        # Service metadata
        self._service_name = "parser_config_manager"
        self._version = "2.0.0"
        
        # Initialize default profiles
        self._initialize_default_profiles()
        
        # Load configuration file if provided
        if self.config_path and self.config_path.exists():
            self.load_configuration_file(self.config_path)
        
        self.logger.info(f"Parser Config Manager v{self._version} initialized")
    
    def _initialize_default_profiles(self):
        """Initialize default configuration profiles"""
        
        # Default profile
        default_config = get_parser_config()
        self._profiles["default"] = ParserConfigProfile(
            name="default",
            description="Default configuration for general use",
            config=default_config
        )
        
        # Development profile
        dev_config = get_parser_config()
        dev_config.debug.debug_mode = True
        dev_config.debug.log_ai_requests = True
        dev_config.cache.enable_caching = True
        dev_config.performance.retry_attempts = 2
        
        self._profiles["development"] = ParserConfigProfile(
            name="development",
            description="Development configuration with debug logging",
            config=dev_config
        )
        
        # Production profile
        prod_config = get_parser_config()
        prod_config.debug.debug_mode = False
        prod_config.debug.log_ai_requests = False
        prod_config.cache.enable_caching = True
        prod_config.performance.retry_attempts = 3
        prod_config.performance.timeout = 60
        
        self._profiles["production"] = ParserConfigProfile(
            name="production",
            description="Production configuration with optimized settings",
            config=prod_config
        )
        
        # Testing profile
        test_config = get_parser_config()
        test_config.models.temperature = 0.0  # Deterministic for testing
        test_config.cache.enable_caching = False
        test_config.performance.retry_attempts = 1
        test_config.performance.timeout = 10
        
        self._profiles["testing"] = ParserConfigProfile(
            name="testing",
            description="Testing configuration with deterministic settings",
            config=test_config
        )
        
        # Integration profile
        integration_config = get_parser_config()
        integration_config.integration_mode = True
        integration_config.debug.log_ai_requests = True
        integration_config.cache.enable_caching = True
        
        self._profiles["integration"] = ParserConfigProfile(
            name="integration",
            description="Integration configuration for main project",
            config=integration_config
        )
    
    @property
    def service_name(self) -> str:
        """Get service name"""
        return self._service_name
    
    @property
    def version(self) -> str:
        """Get service version"""
        return self._version
    
    @property
    def current_profile(self) -> str:
        """Get current configuration profile name"""
        return self._current_profile
    
    def get_config(self) -> ParserConfig:
        """
        Get current configuration.
        
        Returns:
            ParserConfig: Current configuration
        """
        return self._current_config
    
    def get_profile(self, profile_name: str) -> Optional[ParserConfigProfile]:
        """
        Get configuration profile by name.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Optional[ParserConfigProfile]: Profile or None if not found
        """
        return self._profiles.get(profile_name)
    
    def list_profiles(self) -> List[str]:
        """
        Get list of available configuration profiles.
        
        Returns:
            List[str]: List of profile names
        """
        return list(self._profiles.keys())
    
    def get_profile_info(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get profile information.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Optional[Dict[str, Any]]: Profile information or None if not found
        """
        profile = self._profiles.get(profile_name)
        if profile:
            return {
                "name": profile.name,
                "description": profile.description,
                "active": profile_name == self._current_profile
            }
        return None
    
    def switch_profile(self, profile_name: str) -> bool:
        """
        Switch to a different configuration profile.
        
        Args:
            profile_name: Name of the profile to switch to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if profile_name not in self._profiles:
            self.logger.error(f"Profile '{profile_name}' not found")
            return False
        
        try:
            # Switch configuration
            old_profile = self._current_profile
            self._current_config = self._profiles[profile_name].config
            self._current_profile = profile_name
            
            # Notify callbacks
            self._notify_config_change(old_profile, profile_name)
            
            self.logger.info(f"Switched from profile '{old_profile}' to '{profile_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error switching profile: {e}")
            return False
    
    def create_profile(
        self, 
        profile_name: str, 
        description: str, 
        config: ParserConfig
    ) -> bool:
        """
        Create a new configuration profile.
        
        Args:
            profile_name: Name for the new profile
            description: Description of the profile
            config: Configuration for the profile
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate configuration
            if not self.validate_config(config):
                self.logger.error(f"Invalid configuration for profile '{profile_name}'")
                return False
            
            # Create profile
            self._profiles[profile_name] = ParserConfigProfile(
                name=profile_name,
                description=description,
                config=config
            )
            
            self.logger.info(f"Created new profile '{profile_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating profile: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update current configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create updated configuration
            updated_config = self._apply_config_updates(self._current_config, updates)
            
            # Validate updated configuration
            if not self.validate_config(updated_config):
                self.logger.error("Updated configuration is invalid")
                return False
            
            # Apply updates
            old_profile = self._current_profile
            self._current_config = updated_config
            
            # Update current profile
            if self._current_profile in self._profiles:
                self._profiles[self._current_profile].config = updated_config
            
            # Notify callbacks
            self._notify_config_change(old_profile, self._current_profile)
            
            self.logger.info(f"Configuration updated: {list(updates.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def _apply_config_updates(self, config: ParserConfig, updates: Dict[str, Any]) -> ParserConfig:
        """Apply configuration updates to config object"""
        # Convert config to dict
        config_dict = asdict(config)
        
        # Apply updates recursively
        def update_nested_dict(target: dict, source: dict):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_nested_dict(target[key], value)
                else:
                    target[key] = value
        
        update_nested_dict(config_dict, updates)
        
        # Create new config object
        # Note: This is a simplified approach - in practice, you'd want to properly reconstruct the ParserConfig
        # For now, we'll just update the existing config object
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def validate_config(self, config: ParserConfig) -> bool:
        """
        Validate configuration settings.
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required fields
            if not config.models.openai_model:
                raise ValueError("OpenAI model is required")
            
            # Check numeric ranges
            if not (0.0 <= config.models.temperature <= 2.0):
                raise ValueError("OpenAI temperature must be between 0.0 and 2.0")
            
            if not (0.0 <= config.validation.confidence_threshold <= 1.0):
                raise ValueError("Confidence threshold must be between 0.0 and 1.0")
            
            if config.models.max_tokens <= 0:
                raise ValueError("OpenAI max tokens must be positive")
            
            if config.performance.timeout <= 0:
                raise ValueError("Timeout must be positive")
            
            # Check price coefficient ranges
            if config.validation.min_price_coefficient >= config.validation.max_price_coefficient:
                raise ValueError("Min price coefficient must be less than max")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from environment variables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get fresh configuration from environment
            fresh_config = get_parser_config()
            
            # Validate fresh configuration
            if not self.validate_config(fresh_config):
                self.logger.error("Reloaded configuration is invalid")
                return False
            
            # Update current configuration
            old_profile = self._current_profile
            self._current_config = fresh_config
            
            # Update current profile
            if self._current_profile in self._profiles:
                self._profiles[self._current_profile].config = fresh_config
            
            # Notify callbacks
            self._notify_config_change(old_profile, self._current_profile)
            
            self.logger.info("Configuration reloaded from environment")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False
    
    def export_configuration(self, output_path: Union[str, Path]) -> bool:
        """
        Export all configuration profiles to file.
        
        Args:
            output_path: Path for export file
            
        Returns:
            bool: True if successful, False otherwise
        """
        output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create export data
            export_data = {
                "metadata": {
                    "service_name": self.service_name,
                    "version": self.version,
                    "current_profile": self.current_profile,
                    "exported_at": str(Path.cwd())
                },
                "profiles": {
                    name: profile.to_dict() 
                    for name, profile in self._profiles.items()
                }
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuration exported to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, input_path: Union[str, Path]) -> bool:
        """
        Import configuration profiles from file.
        
        Args:
            input_path: Path to import file
            
        Returns:
            bool: True if successful, False otherwise
        """
        input_path = Path(input_path)
        
        try:
            # Check if file exists
            if not input_path.exists():
                self.logger.error(f"Configuration file not found: {input_path}")
                return False
            
            # Load configuration file
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data structure
            if "profiles" not in import_data:
                self.logger.error("Invalid configuration file format")
                return False
            
            # Import profiles
            imported_count = 0
            for profile_name, profile_data in import_data["profiles"].items():
                try:
                    # Create configuration object (simplified)
                    config = get_parser_config()
                    
                    # Create profile
                    profile = ParserConfigProfile(
                        name=profile_data["name"],
                        description=profile_data["description"],
                        config=config
                    )
                    
                    # Validate configuration
                    if self.validate_config(config):
                        self._profiles[profile_name] = profile
                        imported_count += 1
                    else:
                        self.logger.warning(f"Skipped invalid profile: {profile_name}")
                        
                except Exception as e:
                    self.logger.warning(f"Error importing profile {profile_name}: {e}")
            
            self.logger.info(f"Imported {imported_count} configuration profiles")
            return imported_count > 0
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def load_configuration_file(self, file_path: Union[str, Path]) -> bool:
        """
        Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.import_configuration(file_path)
    
    def save_configuration_file(self, file_path: Union[str, Path]) -> bool:
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save file
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.export_configuration(file_path)
    
    def add_change_callback(self, callback: callable) -> None:
        """
        Add callback for configuration changes.
        
        Args:
            callback: Callback function to add
        """
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: callable) -> None:
        """
        Remove callback for configuration changes.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_config_change(self, old_profile: str, new_profile: str) -> None:
        """Notify all callbacks about configuration change"""
        for callback in self._change_callbacks:
            try:
                callback(old_profile, new_profile, self._current_config)
            except Exception as e:
                self.logger.error(f"Error in config change callback: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get configuration manager statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "current_profile": self.current_profile,
            "total_profiles": len(self._profiles),
            "available_profiles": self.list_profiles(),
            "callbacks_registered": len(self._change_callbacks),
            "config_valid": self.validate_config(self._current_config)
        }
    
    @contextmanager
    def temporary_config(self, updates: Dict[str, Any]):
        """
        Context manager for temporary configuration changes.
        
        Args:
            updates: Temporary configuration updates
        """
        # Save current state
        original_config = self._current_config
        original_profile = self._current_profile
        
        try:
            # Apply temporary updates
            self.update_config(updates)
            yield self._current_config
            
        finally:
            # Restore original state
            self._current_config = original_config
            self._current_profile = original_profile


# Service factory
@lru_cache(maxsize=1)
def get_config_manager() -> ParserConfigManager:
    """
    Get Parser Configuration Manager instance (singleton).
    
    Returns:
        ParserConfigManager: Configuration manager instance
    """
    return ParserConfigManager()


# Convenience functions
def get_current_config() -> ParserConfig:
    """
    Get current configuration.
    
    Returns:
        ParserConfig: Current configuration
    """
    manager = get_config_manager()
    return manager.get_config()


def switch_to_profile(profile_name: str) -> bool:
    """
    Switch to configuration profile.
    
    Args:
        profile_name: Name of the profile to switch to
        
    Returns:
        bool: True if successful, False otherwise
    """
    manager = get_config_manager()
    return manager.switch_profile(profile_name)


def validate_configuration(config: ParserConfig) -> bool:
    """
    Validate configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    manager = get_config_manager()
    return manager.validate_config(config) 