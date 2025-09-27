"""
Report Generator Component for Streamlit
Generates various reports and documents
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import io
import json


class ReportGeneratorComponent:
    """Component for generating and exporting various reports."""
    
    def __init__(self):
        """Initialize the report generator component."""
        self.report_types = [
            "Conflict Summary Report",
            "Document Analysis Report", 
            "Usage Statistics Report",
            "Detailed Technical Report"
        ]
    
    def render(self, analysis_results: Dict[str, Any] = None):
        """
        Main render method for the report generator.
        
        Args:
            analysis_results: Analysis results to generate reports from
        """
        self.render_report_generator(analysis_results)
    
    def render_report_generator(self, analysis_data: Dict[str, Any] = None):
        """
        Render the report generation interface.
        
        Args:
            analysis_data: Data from document analysis
        """
        st.subheader("📊 Report Generator")
        
        if not analysis_data:
            st.warning("⚠️ No analysis data available. Please analyze documents first.")
            return
        
        # Report type selection
        selected_type = st.selectbox(
            "Select Report Type:",
            self.report_types,
            help="Choose the type of report to generate"
        )
        
        # Report options
        with st.expander("📝 Report Options", expanded=True):
            self._render_report_options(selected_type)
        
        # Generate report button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📄 Generate Report", type="primary"):
                self._generate_report(selected_type, analysis_data)
    
    def _render_report_options(self, report_type: str):
        """Render report-specific options."""
        
        # Common options
        st.write("**General Options:**")
        col1, col2 = st.columns(2)
        
        with col1:
            include_timestamp = st.checkbox("Include Timestamp", value=True)
            include_summary = st.checkbox("Include Executive Summary", value=True)
        
        with col2:
            include_charts = st.checkbox("Include Charts/Visualizations", value=True)
            include_recommendations = st.checkbox("Include Recommendations", value=True)
        
        # Report-specific options
        if report_type == "Conflict Summary Report":
            st.write("**Conflict Report Options:**")
            col1, col2 = st.columns(2)
            with col1:
                severity_filter = st.multiselect(
                    "Include Severity Levels:",
                    ["High", "Medium", "Low"],
                    default=["High", "Medium", "Low"]
                )
            with col2:
                conflict_types_filter = st.multiselect(
                    "Include Conflict Types:",
                    ["Pricing", "Terms", "Dates", "Contact Info", "Other"],
                    default=["Pricing", "Terms", "Dates", "Contact Info", "Other"]
                )
        
        elif report_type == "Document Analysis Report":
            st.write("**Analysis Report Options:**")
            col1, col2 = st.columns(2)
            with col1:
                include_document_details = st.checkbox("Include Document Details", value=True)
                include_processing_metrics = st.checkbox("Include Processing Metrics", value=True)
            with col2:
                include_confidence_scores = st.checkbox("Include Confidence Scores", value=True)
                include_raw_analysis = st.checkbox("Include Raw Analysis Data", value=False)
        
        elif report_type == "Usage Statistics Report":
            st.write("**Usage Report Options:**")
            col1, col2 = st.columns(2)
            with col1:
                time_period = st.selectbox(
                    "Time Period:",
                    ["Last 24 Hours", "Last Week", "Last Month", "All Time"],
                    index=1
                )
            with col2:
                include_billing = st.checkbox("Include Billing Information", value=True)
                include_trends = st.checkbox("Include Usage Trends", value=True)
    
    def _generate_report(self, report_type: str, analysis_data: Dict[str, Any]):
        """Generate the selected report."""
        
        try:
            if report_type == "Conflict Summary Report":
                report = self._generate_conflict_summary_report(analysis_data)
            elif report_type == "Document Analysis Report":
                report = self._generate_document_analysis_report(analysis_data)
            elif report_type == "Usage Statistics Report":
                report = self._generate_usage_statistics_report(analysis_data)
            elif report_type == "Detailed Technical Report":
                report = self._generate_technical_report(analysis_data)
            else:
                st.error("Invalid report type selected")
                return
            
            # Update usage statistics
            if 'usage_stats' in st.session_state:
                st.session_state.usage_stats['reports_generated'] += 1
            
            # Display report
            st.success("✅ Report generated successfully!")
            
            # Show report preview
            with st.expander("📖 Report Preview", expanded=True):
                st.markdown(report['content'])
            
            # Download options
            self._render_download_options(report, report_type)
            
        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")
    
    def _generate_conflict_summary_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a conflict summary report."""
        
        conflicts = analysis_data.get('conflicts', [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""
# Conflict Summary Report

**Generated:** {timestamp}
**Total Documents Analyzed:** {analysis_data.get('total_documents', 0)}
**Total Conflicts Found:** {len(conflicts)}

## Executive Summary

This report provides a comprehensive overview of conflicts detected during document analysis. 
{len(conflicts)} conflicts were identified across {analysis_data.get('total_documents', 0)} documents.

## Conflict Breakdown

"""
        
        if conflicts:
            # Group conflicts by type
            conflict_types = {}
            for conflict in conflicts:
                c_type = conflict.get('type', 'Unknown')
                if c_type not in conflict_types:
                    conflict_types[c_type] = []
                conflict_types[c_type].append(conflict)
            
            # Add conflict details by type
            for c_type, c_list in conflict_types.items():
                content += f"### {c_type} Conflicts ({len(c_list)})\n\n"
                
                for i, conflict in enumerate(c_list, 1):
                    content += f"**{c_type} #{i}**\n"
                    content += f"- **Description:** {conflict.get('description', 'N/A')}\n"
                    content += f"- **Severity:** {conflict.get('severity', 'Medium')}\n"
                    if conflict.get('confidence'):
                        content += f"- **Confidence:** {conflict['confidence']:.1%}\n"
                    content += "\n"
            
            # Add recommendations
            content += "## Recommendations\n\n"
            recommendations = self._generate_conflict_recommendations(conflicts)
            for i, rec in enumerate(recommendations, 1):
                content += f"{i}. {rec}\n"
        else:
            content += "✅ **No conflicts detected!** All documents appear to be consistent.\n"
        
        return {
            'content': content,
            'type': 'markdown',
            'filename': f'conflict_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        }
    
    def _generate_document_analysis_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed document analysis report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""
# Document Analysis Report

**Generated:** {timestamp}
**Analysis Duration:** {analysis_data.get('processing_time', 0):.2f} seconds

## Analysis Overview

- **Total Documents:** {analysis_data.get('total_documents', 0)}
- **Total Pages Processed:** {analysis_data.get('total_pages', 0)}
- **Average Confidence Score:** {analysis_data.get('average_confidence', 0):.1%}

## Processing Details

### Document Breakdown
"""
        
        documents = analysis_data.get('documents', [])
        for i, doc in enumerate(documents, 1):
            content += f"**Document {i}: {doc.get('name', 'Unknown')}**\n"
            content += f"- Type: {doc.get('type', 'Unknown')}\n"
            content += f"- Pages: {doc.get('pages', 0)}\n"
            content += f"- Processing Time: {doc.get('processing_time', 0):.2f}s\n\n"
        
        # Analysis metrics
        content += "### Analysis Metrics\n\n"
        content += f"- **Text Extraction Success Rate:** {analysis_data.get('extraction_success_rate', 100):.1f}%\n"
        content += f"- **LLM Analysis Calls:** {analysis_data.get('llm_calls', 0)}\n"
        content += f"- **Total Tokens Used:** {analysis_data.get('total_tokens', 0)}\n"
        
        return {
            'content': content,
            'type': 'markdown',
            'filename': f'document_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        }
    
    def _generate_usage_statistics_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a usage statistics report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""
# Usage Statistics Report

**Generated:** {timestamp}

## Current Session Stats

- **Documents Processed:** {analysis_data.get('total_documents', 0)}
- **Processing Time:** {analysis_data.get('processing_time', 0):.2f} seconds
- **API Calls Made:** {analysis_data.get('api_calls', 0)}
- **Tokens Used:** {analysis_data.get('total_tokens', 0)}

## Performance Metrics

- **Average Processing Time per Document:** {analysis_data.get('avg_processing_time', 0):.2f}s
- **Success Rate:** {analysis_data.get('success_rate', 100):.1f}%
- **Conflicts per Document:** {analysis_data.get('conflicts_per_document', 0):.1f}

## Resource Usage

- **Memory Usage:** {analysis_data.get('memory_usage', 'N/A')}
- **CPU Usage:** {analysis_data.get('cpu_usage', 'N/A')}
- **Storage Used:** {analysis_data.get('storage_used', 'N/A')}
"""
        
        return {
            'content': content,
            'type': 'markdown',
            'filename': f'usage_statistics_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        }
    
    def _generate_technical_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed technical report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""
# Detailed Technical Report

**Generated:** {timestamp}

## System Information

- **Platform:** {analysis_data.get('platform', 'Unknown')}
- **Python Version:** {analysis_data.get('python_version', 'Unknown')}
- **Streamlit Version:** {analysis_data.get('streamlit_version', 'Unknown')}

## Processing Pipeline

### 1. Document Ingestion
- **Supported Formats:** PDF, DOCX, TXT
- **Extraction Method:** {analysis_data.get('extraction_method', 'Multi-format')}

### 2. LLM Analysis
- **Model Used:** {analysis_data.get('llm_model', 'GPT-4')}
- **Analysis Type:** {analysis_data.get('analysis_type', 'Conflict Detection')}
- **Confidence Threshold:** {analysis_data.get('confidence_threshold', 0.7):.1%}

### 3. Results Processing
- **Conflict Types Detected:** {len(set(c.get('type', 'Unknown') for c in analysis_data.get('conflicts', [])))}
- **Processing Errors:** {analysis_data.get('processing_errors', 0)}

## Raw Analysis Data

```json
{json.dumps(analysis_data, indent=2, default=str)}
```
"""
        
        return {
            'content': content,
            'type': 'markdown',
            'filename': f'technical_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        }
    
    def _render_download_options(self, report: Dict[str, Any], report_type: str):
        """Render download options for the generated report."""
        
        st.subheader("📥 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download as Markdown
            st.download_button(
                label="📄 Download as Markdown",
                data=report['content'],
                file_name=f"{report['filename']}.md",
                mime="text/markdown"
            )
        
        with col2:
            # Download as TXT
            st.download_button(
                label="📝 Download as Text",
                data=report['content'],
                file_name=f"{report['filename']}.txt",
                mime="text/plain"
            )
        
        with col3:
            # Download as JSON (for technical reports)
            if report_type == "Detailed Technical Report":
                json_data = json.dumps({
                    'report_type': report_type,
                    'generated_at': datetime.now().isoformat(),
                    'content': report['content']
                }, indent=2)
                
                st.download_button(
                    label="📊 Download as JSON",
                    data=json_data,
                    file_name=f"{report['filename']}.json",
                    mime="application/json"
                )
    
    def _generate_conflict_recommendations(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on conflicts."""
        recommendations = []
        conflict_types = [c.get('type', '').lower() for c in conflicts]
        
        if any('pricing' in ct for ct in conflict_types):
            recommendations.append("Review and standardize pricing information across all documents")
        
        if any('term' in ct for ct in conflict_types):
            recommendations.append("Align contract terms and conditions to ensure consistency")
        
        if any('date' in ct or 'deadline' in ct for ct in conflict_types):
            recommendations.append("Verify and update all dates and deadlines")
        
        if any('contact' in ct for ct in conflict_types):
            recommendations.append("Update contact information to reflect current details")
        
        if len(conflicts) > 10:
            recommendations.append("Consider document consolidation to reduce conflict complexity")
        
        recommendations.append("Implement a document review process to prevent future conflicts")
        
        return recommendations
