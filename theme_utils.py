"""
Theme utilities for David Lynch Collection Dashboard
Handles dynamic theme detection and AgGrid styling
"""

import streamlit as st

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
        """Detect current Streamlit theme with fallback"""
        
        # Check if user manually set preference
        if hasattr(st.session_state, 'theme_preference'):
            return st.session_state.theme_preference
        
        # Default to light theme for now
        return 'light'
    
    def get_theme_css(self, theme_name):
        """Generate CSS for AgGrid theming with maximum override force"""
        theme = self.themes.get(theme_name, self.themes['light'])
        colors = theme['colors']
        
        return f"""
        <style>
        /* Nuclear option - override everything AgGrid related */
        div[data-testid="stAgGrid"] {{
            background-color: {colors['background']} !important;
        }}
        
        div[data-testid="stAgGrid"] > div {{
            background-color: {colors['background']} !important;
        }}
        
        /* Target all possible AgGrid containers */
        .ag-theme-alpine,
        .ag-theme-balham,
        .ag-theme-alpine *,
        .ag-theme-balham * {{
            background-color: {colors['background']} !important;
            color: {colors['text']} !important;
        }}
        
        /* Specific overrides for main containers */
        .ag-root-wrapper,
        .ag-root,
        .ag-body-viewport,
        .ag-center-cols-container,
        .ag-body-horizontal-scroll-viewport,
        .ag-body-vertical-scroll-viewport {{
            background-color: {colors['background']} !important;
            color: {colors['text']} !important;
        }}
        
        /* Row overrides */
        .ag-row,
        .ag-row-even,
        .ag-row-odd,
        .ag-cell {{
            background-color: {colors['background']} !important;
            color: {colors['text']} !important;
            border-color: {colors['border']} !important;
        }}
        
        /* Alternate row coloring for better visibility */
        .ag-row-odd .ag-cell {{
            background-color: {colors['surface']} !important;
        }}
        
        /* Header styling */
        .ag-header,
        .ag-header-row,
        .ag-header-cell {{
            background-color: {colors['header']} !important;
            color: {colors['text']} !important;
            border-color: {colors['border']} !important;
        }}
        
        .ag-header-cell-label {{
            color: {colors['text']} !important;
            font-weight: 600 !important;
        }}
        
        /* Pagination */
        .ag-paging-panel {{
            background-color: {colors['surface']} !important;
            color: {colors['text']} !important;
            border-color: {colors['border']} !important;
        }}
        
        /* Links remain red */
        .ag-cell a {{
            color: #ff4b4b !important;
        }}
        </style>
        """
    
    def get_aggrid_theme(self):
        """Get the appropriate AgGrid theme as string"""
        current_theme = self.get_current_theme()
        if current_theme == 'dark':
            return 'streamlit'  # Try streamlit theme instead of balham
        else:
            return 'alpine'

# Global theme manager instance
theme_manager = ThemeManager()

# Simple function for manual theme testing
def toggle_theme():
    """Toggle between light and dark theme for testing"""
    current = theme_manager.get_current_theme()
    st.session_state.theme_preference = 'dark' if current == 'light' else 'light'