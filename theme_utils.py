"""
Theme utilities for David Lynch Collection Dashboard
Handles dynamic theme detection and AgGrid styling
"""

import streamlit as st
from st_aggrid import AgGridTheme

class ThemeManager:
    """Manages theme detection and AgGrid styling"""
    
    def __init__(self):
        self.themes = {
            'light': {
                'aggrid_theme': 'alpine',
                'colors': {
                    'background': '#ffffff',
                    'surface': '#f8f9fa',
                    'header': '#e9ecef',
                    'text': '#212529',
                    'border': '#dee2e6',
                    'hover': '#f8f9fa',
                    'selected': '#e7f3ff'
                }
            },
            'dark': {
                'aggrid_theme': 'balham',
                'colors': {
                    'background': '#0e1117',
                    'surface': '#262730',
                    'header': '#3d4043',
                    'text': '#fafafa',
                    'border': '#4a4a4a',
                    'hover': '#262730',
                    'selected': '#1e3a5f'
                }
            }
        }
    
    def get_current_theme(self):
        """Detect current Streamlit theme with fallbacks"""
        try:
            # Try official API first (Streamlit 1.46.0+)
            if hasattr(st.context, 'theme'):
                return st.context.theme.type
        except:
            pass
        
        try:
            # Fallback: Check session state for user preference
            if 'theme_preference' in st.session_state:
                return st.session_state.theme_preference
        except:
            pass
        
        # Default fallback
        return 'light'
    
    @st.cache_data
    def get_theme_css(_self, theme_name):
        """Generate cached CSS for AgGrid theming"""
        theme = _self.themes.get(theme_name, _self.themes['light'])
        colors = theme['colors']
        
        return f"""
        <style>
        /* AgGrid theme customization */
        .ag-theme-{theme['aggrid_theme']} {{
            --ag-background-color: {colors['background']};
            --ag-foreground-color: {colors['text']};
            --ag-header-background-color: {colors['header']};
            --ag-header-foreground-color: {colors['text']};
            --ag-border-color: {colors['border']};
            --ag-row-hover-color: {colors['hover']};
            --ag-selected-row-background-color: {colors['selected']};
            --ag-cell-horizontal-border: 1px solid {colors['border']};
            --ag-row-border-color: {colors['border']};
            border-radius: 8px;
            font-family: "Source Sans Pro", sans-serif;
        }}
        
        /* Header styling */
        .ag-theme-{theme['aggrid_theme']} .ag-header {{
            border-bottom: 2px solid {colors['border']};
        }}
        
        .ag-theme-{theme['aggrid_theme']} .ag-header-cell-label {{
            color: {colors['text']} !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }}
        
        /* Cell styling */
        .ag-theme-{theme['aggrid_theme']} .ag-cell {{
            border-right: 1px solid {colors['border']};
            display: flex !important;
            align-items: center !important;
        }}
        
        /* Pagination styling */
        .ag-theme-{theme['aggrid_theme']} .ag-paging-panel {{
            background-color: {colors['surface']};
            border-top: 1px solid {colors['border']};
            color: {colors['text']};
        }}
        
        /* Links and buttons */
        .ag-theme-{theme['aggrid_theme']} a {{
            color: #ff4b4b !important;
            text-decoration: none;
        }}
        
        .ag-theme-{theme['aggrid_theme']} a:hover {{
            text-decoration: underline;
        }}
        </style>
        """
    
    def get_aggrid_theme(self):
        """Get the appropriate AgGrid theme enum"""
        current_theme = self.get_current_theme()
        theme_name = self.themes[current_theme]['aggrid_theme']
        
        # Map string to AgGridTheme enum
        theme_map = {
            'alpine': AgGridTheme.ALPINE,
            'balham': AgGridTheme.BALHAM,
            'material': AgGridTheme.MATERIAL,
            'streamlit': AgGridTheme.STREAMLIT
        }
        
        return theme_map.get(theme_name, AgGridTheme.ALPINE)

# Global theme manager instance
theme_manager = ThemeManager()