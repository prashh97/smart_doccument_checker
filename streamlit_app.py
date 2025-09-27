"""
Smart Doc Checker Agent - Main Streamlit Application
Entry point for the document conflict detection system
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import custom modules
from src.document_processor import DocumentProcessor
from src.llm_analyser import EnhancedConflictAnalyzer
# Optional imports for development
try:
    from src.flexprice import FlexpriceClient
except ImportError:
    FlexpriceClient = None

try:
    from pathway_monitor import PathwayMonitor
except ImportError:
    PathwayMonitor = None

# Import UI components
from components.file_uploader import FileUploaderComponent
from components.conflict_display import ConflictDisplayComponent
from components.usage import UsageDashboardComponent
from components.report_generator import ReportGeneratorComponent

# Import configuration
from config.settings import AppSettings

# Page configuration
st.set_page_config(
    page_title="Smart Doc Checker Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'usage_stats' not in st.session_state:
        st.session_state.usage_stats = {
            'docs_analyzed': 0,
            'reports_generated': 0,
            'total_conflicts_found': 0
        }
    if 'flexprice_events' not in st.session_state:
        st.session_state.flexprice_events = []
    if 'pathway_status' not in st.session_state:
        st.session_state.pathway_status = {'connected': False, 'last_update': None}
    if 'billing_session' not in st.session_state:
        st.session_state.billing_session = {
            'session_id': 'default_session',
            'start_time': '2024-01-01T00:00:00Z',
            'customer_id': 'demo_user',
            'total_amount': 0.0
        }
    if 'app_settings' not in st.session_state:
        st.session_state.app_settings = AppSettings()
    
    # Always ensure the API key is set (in case it gets reset)
    st.session_state.app_settings.GEMINI_API_KEY = "AIzaSyBBJ5gMwH0AsuBN92G5i35-zoSEwVq5pWY"

def get_app_components():
    """Initialize and cache application components"""
    components = {
        'document_processor': DocumentProcessor(),
        'llm_analyzer': EnhancedConflictAnalyzer(),
        'flexprice_client': FlexpriceClient() if FlexpriceClient else None,
        'pathway_monitor': PathwayMonitor(),
        'file_uploader': FileUploaderComponent(),
        'conflict_display': ConflictDisplayComponent(),
        'usage_dashboard': UsageDashboardComponent(),
        'report_generator': ReportGeneratorComponent()
    }
    return components

def main():
    """Main application function"""
    
    # Initialize session state FIRST
    initialize_session_state()
    
    # Get cached components AFTER session state is initialized
    components = get_app_components()
    
    # App header
    st.title("🔍 Smart Doc Checker Agent")
    st.markdown("**Automatically detect contradictions and conflicts across multiple documents using AI**")
    
    # Sidebar with API configuration and usage dashboard
    with st.sidebar:
        # API Configuration Section
        st.subheader("🔑 API Status")
        
        # Check if API keys are configured
        api_validations = st.session_state.app_settings.validate_api_keys()
        
        # Show API status
        for service, is_valid in api_validations.items():
            status = "✅" if is_valid else "❌"
            st.write(f"{status} {service.title()}")
        
        if api_validations.get('gemini', False):
            st.success("🤖 AI Analysis Ready!")
        else:
            st.warning("⚠️ Gemini API not configured")
        
        st.divider()
        components['usage_dashboard'].render()
        st.divider()
        components['pathway_monitor'].render_monitor_status()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # File upload section
        uploaded_files = components['file_uploader'].render()
        
        if uploaded_files:
            # Analysis controls
            selected_model = st.selectbox(
                "Select AI Model",
                ["gemini-2.5-flash", "gemini-pro", "grok (coming soon)"],
                help="Choose the AI model for document analysis"
            )
            
            analysis_type = st.radio(
                "Analysis Depth",
                ["Quick Scan", "Comprehensive Analysis"],
                help="Quick scan for obvious conflicts, comprehensive for detailed analysis"
            )
            
            if st.button("🔍 Analyze Documents", type="primary"):
                analyze_documents(uploaded_files, selected_model, analysis_type.lower(), components)
    
    with col2:
        # Results display section
        if st.session_state.analysis_results and 'conflicts' in st.session_state.analysis_results:
            components['conflict_display'].render(st.session_state.analysis_results)
            
            # Report generation section
            if st.session_state.analysis_results['conflicts']:
                components['report_generator'].render(st.session_state.analysis_results)
        else:
            st.info("Upload documents and click 'Analyze Documents' to detect conflicts")

def analyze_documents(uploaded_files, selected_model, analysis_type, components):
    """Process uploaded documents and detect conflicts"""
    
    # Check if API keys are configured
    api_validations = st.session_state.app_settings.validate_api_keys()
    
    if not api_validations.get('gemini', False):
        st.error("❌ **Gemini API key not configured!**")
        st.info("👈 Configure your API key in the sidebar to enable AI analysis.")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Process uploaded files
        status_text.text("📄 Extracting text from documents...")
        progress_bar.progress(20)
        
        documents = components['document_processor'].process_uploaded_files(uploaded_files)
        
        # Step 2: Track billing (optional)
        status_text.text("💰 Processing billing...")
        progress_bar.progress(35)
        
        try:
            analysis_cost = components['flexprice_client'].track_document_analysis(len(uploaded_files))
        except Exception as e:
            st.warning(f"Billing tracking unavailable: {str(e)}")
            analysis_cost = 0.0
        
        # Step 3: LLM Analysis
        status_text.text(f"🤖 Analyzing with {selected_model.upper()}...")
        progress_bar.progress(60)
        
        conflicts = components['llm_analyzer'].analyze_documents_for_conflicts(
            documents, 
            model=selected_model,
            analysis_type=analysis_type
        )
        
        # Step 4: Generate summary
        status_text.text("📊 Generating insights...")
        progress_bar.progress(85)
        
        analysis_summary = components['llm_analyzer'].get_analysis_summary(conflicts)
        
        # Step 5: Update results
        status_text.text("✅ Analysis complete!")
        progress_bar.progress(100)
        
        # Store results
        st.session_state.analysis_results = {
            'documents': documents,
            'conflicts': conflicts,
            'analysis_cost': analysis_cost,
            'selected_model': selected_model,
            'analysis_type': analysis_type,
            'analysis_summary': analysis_summary,
            'timestamp': components['document_processor'].get_current_timestamp()
        }
        
        # Update usage stats
        st.session_state.usage_stats['docs_analyzed'] += len(uploaded_files)
        st.session_state.usage_stats['total_conflicts_found'] += len(conflicts)
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        # Success message
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"✅ Analysis Complete!")
        with col2:
            st.info(f"🤖 {selected_model}")
        with col3:
            st.metric("Conflicts Found", len(conflicts))
        
        # Show top recommendations
        if analysis_summary.get('recommendations'):
            st.subheader("🎯 Key Recommendations")
            for rec in analysis_summary['recommendations'][:3]:
                st.write(f"• {rec}")
                
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Analysis failed: {str(e)}")
        st.error("Please check your API keys and try again.")

if __name__ == "__main__":
    main()