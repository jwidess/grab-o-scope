import json
import os

class ConfigManager:
    """Manages application settings and configurations."""

    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Load settings from the configuration file."""
        try:
            with open(self.config_file, 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            # Create default settings
            self.settings = {
                'instrument_name': '',
                'output_filename': 'grab-o-scope.png',
                'output_directory': '',
                'trace_mode': False
            }
            self.save_settings()
        except json.JSONDecodeError:
            self.settings = {}

    def save_settings(self):
        """Save the current settings to the configuration file."""
        with open(self.config_file, 'w') as file:
            json.dump(self.settings, file, indent=4)

    def get_setting(self, key, default=None):
        """Get a setting value by key."""
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """Set a setting value by key."""
        self.settings[key] = value
        self.save_settings()
    
    # Aliases for consistency with main_window.py
    def load_config(self):
        """Alias for load_settings - returns the settings dict"""
        self.load_settings()
        return self.settings
    
    def save_config(self, config_data):
        """Alias for save_settings - accepts a dict to save"""
        self.settings = config_data
        self.save_settings()