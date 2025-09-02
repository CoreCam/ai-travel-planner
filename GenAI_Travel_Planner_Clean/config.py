"""
Configuration management for AI Travel Planner
Handles environment variables and API keys securely for both local and Streamlit Cloud deployment
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_api_key(key_name):
    """
    Get API key from Streamlit secrets or environment variables
    
    Args:
        key_name (str): API key name
    
    Returns:
        str: API key value or None if not found
    """
    # First try Streamlit secrets (for deployed apps)
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    
    # Fallback to environment variables (for local development)
    return os.getenv(key_name)

# API Configuration
class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = get_api_key("OPENAI_API_KEY")
    
    # Google APIs Configuration
    GOOGLE_API_KEY = get_api_key("GOOGLE_API_KEY")
    GOOGLE_PLACES_API_KEY = get_api_key("GOOGLE_PLACES_API_KEY")
    
    # Amadeus Travel API Configuration
    AMADEUS_CLIENT_ID = get_api_key("AMADEUS_CLIENT_ID")
    AMADEUS_CLIENT_SECRET = get_api_key("AMADEUS_CLIENT_SECRET")
    
    # SerpAPI Configuration (Optional)
    SERPAPI_KEY = get_api_key("SERPAPI_KEY")
    
    # RapidAPI Configuration for Kiwi.com & Skyscanner (Primary flight search)
    # Get your free API key from: https://rapidapi.com/emir12/api/kiwi-com-cheap-flights/
    RAPIDAPI_KEY = get_api_key("RAPIDAPI_KEY")
    
    @classmethod
    def validate_required_keys(cls):
        """
        Validate that all required API keys are present
        
        Returns:
            tuple: (bool, list) - (all_valid, missing_keys)
        """
        required_keys = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "GOOGLE_API_KEY": cls.GOOGLE_API_KEY,
            "GOOGLE_PLACES_API_KEY": cls.GOOGLE_PLACES_API_KEY,
            "AMADEUS_CLIENT_ID": cls.AMADEUS_CLIENT_ID,
            "AMADEUS_CLIENT_SECRET": cls.AMADEUS_CLIENT_SECRET,
        }
        
        missing_keys = [key for key, value in required_keys.items() if not value]
        return len(missing_keys) == 0, missing_keys
    
    @classmethod
    def display_setup_instructions(cls):
        """
        Display setup instructions for missing API keys
        """
        is_valid, missing_keys = cls.validate_required_keys()
        
        if not is_valid:
            st.error("🔑 Missing Required API Keys")
            st.markdown("The following API keys are missing:")
            
            for key in missing_keys:
                st.write(f"❌ **{key}**")
            
            st.info("""
            📝 **Setup Instructions:**
            
            **For Streamlit Cloud:**
            1. Click 'Manage app' → 'Secrets' tab
            2. Add each key in this format (without quotes around key names):
            ```
            OPENAI_API_KEY = "your_openai_key_here"
            GOOGLE_API_KEY = "your_google_key_here"
            GOOGLE_PLACES_API_KEY = "your_google_places_key_here"
            AMADEUS_CLIENT_ID = "your_amadeus_id_here"
            AMADEUS_CLIENT_SECRET = "your_amadeus_secret_here"
            SERPAPI_KEY = "your_serpapi_key_here"
            ```
            
            **For Local Development:**
            Create a `.env` file in your project directory with the same keys.
            """)
            
            st.markdown("### � **Get API Keys:**")
            st.markdown("- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)")
            st.markdown("- **Google APIs**: [console.cloud.google.com](https://console.cloud.google.com/)")
            st.markdown("- **Amadeus**: [developers.amadeus.com](https://developers.amadeus.com/)")
            st.markdown("- **SerpAPI**: [serpapi.com](https://serpapi.com/) (optional)")
            
            return False
        
        return True

# Export config instance
config = Config()
