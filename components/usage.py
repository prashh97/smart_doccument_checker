"""
Usage Dashboard Component for Streamlit Sidebar
"""

import streamlit as st
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

from src.flexprice import FlexpriceClient, BillingDashboard

class UsageDashboardComponent:
    """Usage and billing dashboard for sidebar"""
    
    def __init__(self):
        self.flexprice_client = FlexpriceClient()
        self.billing_dashboard = BillingDashboard(self.flexprice_client)
    
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
            'total_conflicts_found': 0,
            'billing_amount': 0.0
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
        
        st.metric(
            "Session Cost",
            f"${usage_stats.get('billing_amount', 0.0):.2f}",
            help="Total cost for current session"
        )
        
        # API Connection Status
        api_status = self.flexprice_client.validate_api_connection()
        status_emoji = {
            "connected": "🟢",
            "mock": "🟡", 
            "error": "🔴"
        }
        
        st.metric(
            "Billing API",
            f"{status_emoji.get(api_status['status'], '❓')} {api_status['status'].title()}",
            help=api_status['message']
        )
    
    def _render_usage_breakdown(self):
        """Render usage breakdown with charts"""
        
        usage_summary = self.flexprice_client.get_usage_summary()
        
        if usage_summary['total_events'] > 0:
            st.subheader("Usage Breakdown")
            
            # Events by type pie chart
            events_by_type = usage_summary.get('events_by_type', {})
            
            if events_by_type:
                # Prepare data for chart
                labels = list(events_by_type.keys())
                values = list(events_by_type.values())
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                
                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    marker_colors=colors[:len(labels)]
                )])
                
                fig.update_layout(
                    title="Usage by Event Type",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            # Usage timeline
            events = self.flexprice_client.get_usage_events()
            if events:
                st.subheader("Usage Timeline")
                
                # Convert to DataFrame for easier plotting
                df = pd.DataFrame(events)
                if not df.empty and 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df_hourly = df.groupby([df['timestamp'].dt.hour, 'event_type']).size().reset_index(name='count')
                    
                    fig = px.line(df_hourly, x='timestamp', y='count', color='event_type',
                                title="Usage Over Time")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No usage data available yet. Start analyzing documents to see your usage statistics!")
    
    def _render_cost_estimator(self):
        """Render cost estimation calculator"""
        
        st.write("**Estimate Processing Costs**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_docs = st.number_input(
                "Number of Documents",
                min_value=1,
                max_value=100,
                value=5,
                help="Estimate cost for processing this many documents"
            )
            
            avg_pages = st.number_input(
                "Average Pages per Document",
                min_value=1,
                max_value=500,
                value=10,
                help="Average number of pages per document"
            )
        
        with col2:
            complexity = st.selectbox(
                "Document Complexity",
                ["Simple", "Medium", "Complex"],
                index=1,
                help="Simple: Text-only, Medium: Mixed content, Complex: Heavy formatting"
            )
            
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Basic Conflict Check", "Detailed Analysis", "Full Report"],
                index=1,
                help="Type of analysis to perform"
            )
        
        # Cost calculation logic
        base_cost_per_page = {
            "Simple": 0.01,
            "Medium": 0.02,
            "Complex": 0.03
        }
        
        analysis_multiplier = {
            "Basic Conflict Check": 1.0,
            "Detailed Analysis": 1.5,
            "Full Report": 2.0
        }
        
        total_pages = num_docs * avg_pages
        base_cost = total_pages * base_cost_per_page[complexity]
        final_cost = base_cost * analysis_multiplier[analysis_type]
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Pages", total_pages)
        
        with col2:
            st.metric("Base Cost", f"${base_cost:.2f}")
        
        with col3:
            st.metric("Estimated Total", f"${final_cost:.2f}", delta=f"+{((analysis_multiplier[analysis_type] - 1) * 100):.0f}%")
        
        if st.button("💳 Start Analysis", type="primary", use_container_width=True):
            st.success("Analysis started! Upload your documents to begin.")
    
    def _render_settings(self):
        """Render API settings and controls"""
        
        st.write("**API Configuration**")
        
        # API Key status
        api_config = self.flexprice_client.settings.get_flexprice_config()
        
        if api_config['api_key']:
            st.success(f"✅ API Key configured ({api_config['api_key'][:8]}...)")
        else:
            st.warning("⚠️ No API key configured")
            st.info("Add your Flexprice API key to enable billing tracking")
        
        # Connection test
        if st.button("🔄 Test API Connection", use_container_width=True):
            with st.spinner("Testing connection..."):
                result = self.flexprice_client.validate_api_connection()
                
                if result['status'] == 'connected':
                    st.success(f"✅ {result['message']}")
                elif result['status'] == 'mock':
                    st.info(f"ℹ️ {result['message']}")
                else:
                    st.error(f"❌ {result['message']}")
        
        st.divider()
        
        # Usage controls
        st.write("**Usage Controls**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Refresh Stats", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Session", use_container_width=True):
                # Reset session usage stats
                st.session_state.usage_stats = {
                    'docs_analyzed': 0,
                    'reports_generated': 0,
                    'total_conflicts_found': 0,
                    'billing_amount': 0.0
                }
                st.success("Session data cleared!")
                st.rerun()
        
        # Debug information  
        app_settings = st.session_state.get('app_settings')
        if app_settings and hasattr(app_settings, 'DEBUG') and app_settings.DEBUG:
            with st.expander("🔍 Debug Information"):
                st.write("**Current Session State:**")
                st.json(st.session_state.get('usage_stats', {}))
                
                st.write("**API Configuration:**")
                st.json(api_config)