"""
Application Settings and Configuration Management
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any
import os

class AppSettings:
    """Centralized application settings"""
    
    def __init__(self):
        self.load_settings()
    
    def load_settings(self):
        """Load settings from Streamlit secrets and environment"""
        import os
        
        # Try to load from secrets, fall back to environment variables and defaults
        try:
            api_keys = st.secrets.get("api_keys", {})
            app_settings = st.secrets.get("app_settings", {})
            pathway_settings = st.secrets.get("pathway_settings", {})
        except:
            # If secrets are not available, use empty dictionaries
            api_keys = {}
            app_settings = {}
            pathway_settings = {}
        
        # API Keys (with environment variable fallback)
        self.GEMINI_API_KEY = api_keys.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        self.OPENAI_API_KEY = api_keys.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.GROK_API_KEY = api_keys.get("GROK_API_KEY", os.getenv("GROK_API_KEY", ""))
        self.FLEXPRICE_API_KEY = api_keys.get("FLEXPRICE_API_KEY", os.getenv("FLEXPRICE_API_KEY", ""))
        
        # App Settings
        self.DEBUG = app_settings.get("DEBUG", os.getenv("DEBUG", "false").lower() == "true")
        self.MAX_FILE_SIZE = app_settings.get("MAX_FILE_SIZE", int(os.getenv("MAX_FILE_SIZE", "50")))  # MB
        self.MAX_FILES_PER_ANALYSIS = app_settings.get("MAX_FILES_PER_ANALYSIS", int(os.getenv("MAX_FILES_PER_ANALYSIS", "5")))
        self.DEFAULT_MODEL = app_settings.get("DEFAULT_MODEL", os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"))
        
        # Pathway Settings
        self.PATHWAY_LICENSE_KEY = pathway_settings.get("PATHWAY_LICENSE_KEY", os.getenv("PATHWAY_LICENSE_KEY", ""))
        self.EXTERNAL_MONITOR_URL = pathway_settings.get("EXTERNAL_MONITOR_URL", os.getenv("EXTERNAL_MONITOR_URL", ""))
        self.MONITOR_INTERVAL = pathway_settings.get("MONITOR_INTERVAL", int(os.getenv("MONITOR_INTERVAL", "30")))
        
        # UI Settings
        try:
            ui_settings = st.secrets.get("ui_settings", {})
        except:
            ui_settings = {}
        
        self.APP_TITLE = ui_settings.get("APP_TITLE", os.getenv("APP_TITLE", "Smart Doc Checker Agent"))
        self.COMPANY_NAME = ui_settings.get("COMPANY_NAME", os.getenv("COMPANY_NAME", "Your Company"))
        self.SUPPORT_EMAIL = ui_settings.get("SUPPORT_EMAIL", os.getenv("SUPPORT_EMAIL", "support@example.com"))
        
        # Directories
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.UPLOADS_DIR = self.DATA_DIR / "uploads"
        self.REPORTS_DIR = self.DATA_DIR / "reports"
        self.CACHE_DIR = self.DATA_DIR / "cache"
        
        # Create directories if they don't exist
        self.create_directories()
        
        # Pricing
        self.PRICING = {
            "document_analysis": 0.10,  # per document
            "report_generation": 0.25,  # per report
            "premium_analysis": 0.50    # for advanced features
        }
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.DATA_DIR,
            self.UPLOADS_DIR,
            self.REPORTS_DIR,
            self.CACHE_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for specific LLM model"""
        
        model_configs = {
            "gemini-2.5-flash": {
                "api_key": self.GEMINI_API_KEY,
                "max_tokens": 1000000,  # 1M token context
                "cost_per_input_token": 0.15 / 1000000,   # $0.15/M
                "cost_per_output_token": 0.60 / 1000000   # $0.60/M
            },
            "gemini-pro": {
                "api_key": self.GEMINI_API_KEY,
                "max_tokens": 128000,
                "cost_per_input_token": 0.50 / 1000000,
                "cost_per_output_token": 1.50 / 1000000
            },
            "grok": {
                "api_key": self.GROK_API_KEY,
                "max_tokens": 128000,
                "cost_per_input_token": 0.30 / 1000000,  # Estimate
                "cost_per_output_token": 1.20 / 1000000   # Estimate
            }
        }
        
        return model_configs.get(model_name, model_configs["gemini-2.5-flash"])
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate API keys are present"""
        
        validations = {
            "gemini": bool(self.GEMINI_API_KEY),
            "flexprice": bool(self.FLEXPRICE_API_KEY),
            "pathway": bool(self.PATHWAY_LICENSE_KEY)
        }
        
        return validations
    
    def get_supported_file_types(self) -> Dict[str, list]:
        """Get supported file types for upload"""
        
        return {
            "text": [".txt", ".md", ".rtf"],
            "pdf": [".pdf"],
            "word": [".docx", ".doc"],
            "other": [".html", ".xml"]
        }
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG
    
    def get_flexprice_config(self) -> Dict[str, str]:
        """Get Flexprice configuration"""
        
        # Try to get base URL from secrets, fall back to environment or default
        try:
            base_url = st.secrets.get("api_keys", {}).get("FLEXPRICE_BASE_URL", "https://api.flexprice.com/v1")
        except:
            base_url = os.getenv("FLEXPRICE_BASE_URL", "https://api.flexprice.com/v1")
        
        return {
            "api_key": self.FLEXPRICE_API_KEY,
            "base_url": base_url
        }