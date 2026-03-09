"""
Usage Dashboard Component for Streamlit Sidebar
"""

import streamlit as st
from typing import Dict, Any
from datetime import datetime
import pandas as pd

# Optional plotly imports for advanced charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    px = None
    go = None
    PLOTLY_AVAILABLE = False

class UsageDashboardComponent:
    """Usage and billing dashboard for sidebar"""
    
    def __init__(self):
        pass
    
    def render(self):
        """Render the complete usage dashboard"""
        
        st.header("📊 Usage Dashboard")
        
        # Main usage metrics
        self._render_main_metrics()
        
        # Usage breakdown
        self._render_usage_breakdown()
        
        # Cost estimator
        with st.expander("💰 Cost Calculator"):
            self._render_cost_estimator()
        
        # API status and controls
        with st.expander("⚙️ Settings"):
            self._render_settings()
    
    def _render_main_metrics(self):
        """Render main usage metrics"""
        
        usage_stats = st.session_state.get('usage_stats', {
            'docs_analyzed': 0,
            'reports_generated': 0,
            'total_conflicts_found': 0
        })
        
        # Primary metrics
        st.metric(
            "Documents Analyzed",
            usage_stats.get('docs_analyzed', 0),
            help="Total number of documents processed in this session"
        )
        
        st.metric(
            "Reports Generated", 
            usage_stats.get('reports_generated', 0),
            help="Number of detailed reports created"
        )
        
        st.metric(
            "Conflicts Found",
            usage_stats.get('total_conflicts_found', 0),
            help="Total conflicts detected across all analyses"
        )
    
    def _render_usage_breakdown(self):
        """Render usage breakdown with charts"""
        
        usage_stats = st.session_state.get('usage_stats', {
            'docs_analyzed': 0,
            'reports_generated': 0,
            'total_conflicts_found': 0
        })
        
        if usage_stats.get('docs_analyzed', 0) > 0:
            st.subheader("Usage Breakdown")
            
            # Simple breakdown
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Avg Conflicts per Doc", 
                         round(usage_stats.get('total_conflicts_found', 0) / max(usage_stats.get('docs_analyzed', 1), 1), 1))
            with col2:
                st.metric("Reports per Analysis",
                         round(usage_stats.get('reports_generated', 0) / max(usage_stats.get('docs_analyzed', 1), 1), 1))
        else:
            st.info("No usage data available yet. Start analyzing documents to see your usage statistics!")
    
    def _render_cost_estimator(self):
        """Render cost estimation calculator"""
        
        st.write("**Cost Estimation**")
        st.info("Cost tracking is currently disabled. Contact support for billing information.")
        
        # Simple placeholder
        st.metric("Estimated Cost per Analysis", "Free", help="No cost tracking enabled")
    
    def _render_settings(self):
        """Render API settings and controls"""
        
        st.write("**API Configuration**")
        st.info("Billing integration is currently disabled.")
        
        # Show Gemini API status
        gemini_key = st.session_state.app_settings.GEMINI_API_KEY
        if gemini_key:
            st.success("✅ Gemini API configured")
        else:
            st.warning("⚠️ Gemini API key not configured")