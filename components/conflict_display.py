"""
Conflict Display Component for Streamlit
Displays document conflicts and analysis results
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime


class ConflictDisplayComponent:
    """Component for displaying document conflicts and analysis results."""
    
    def __init__(self):
        """Initialize the conflict display component."""
        self.conflicts = []
        self.current_analysis = None
    
    def render_conflicts(self, conflicts: List[Dict[str, Any]]):
        """
        Render conflicts in the main display area.
        
        Args:
            conflicts: List of conflict dictionaries
        """
        if not conflicts:
            st.info("🎉 No conflicts detected in the analyzed documents!")
            return
        
        st.subheader(f"⚠️ {len(conflicts)} Conflict(s) Detected")
        
        for i, conflict in enumerate(conflicts, 1):
            with st.expander(f"Conflict #{i}: {conflict.get('type', 'Unknown')}", expanded=i==1):
                self._render_single_conflict(conflict)
    
    def _render_single_conflict(self, conflict: Dict[str, Any]):
        """Render a single conflict with details."""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Description:**")
            st.write(conflict.get('description', 'No description available'))
            
            if conflict.get('details'):
                st.write("**Details:**")
                st.write(conflict['details'])
            
            if conflict.get('affected_sections'):
                st.write("**Affected Sections:**")
                for section in conflict['affected_sections']:
                    st.write(f"- {section}")
        
        with col2:
            # Display conflict metadata
            st.write("**Conflict Info:**")
            st.write(f"Type: {conflict.get('type', 'Unknown')}")
            st.write(f"Severity: {conflict.get('severity', 'Medium')}")
            
            if conflict.get('confidence'):
                st.metric("Confidence", f"{conflict['confidence']:.1%}")
            
            if conflict.get('source_documents'):
                st.write("**Source Documents:**")
                for doc in conflict['source_documents']:
                    st.write(f"📄 {doc}")
    
    def render_analysis_summary(self, analysis: Dict[str, Any]):
        """
        Render analysis summary with statistics.
        
        Args:
            analysis: Analysis results dictionary
        """
        if not analysis:
            return
        
        st.subheader("📊 Analysis Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Documents", 
                analysis.get('total_documents', 0)
            )
        
        with col2:
            st.metric(
                "Conflicts Found", 
                analysis.get('total_conflicts', 0),
                delta=None
            )
        
        with col3:
            st.metric(
                "Processing Time", 
                f"{analysis.get('processing_time', 0):.2f}s"
            )
        
        with col4:
            confidence = analysis.get('average_confidence', 0)
            st.metric(
                "Avg Confidence", 
                f"{confidence:.1%}" if confidence else "N/A"
            )
    
    def render_conflict_types_chart(self, conflicts: List[Dict[str, Any]]):
        """Render a chart showing conflict types distribution."""
        if not conflicts:
            return
        
        # Count conflict types
        type_counts = {}
        for conflict in conflicts:
            conflict_type = conflict.get('type', 'Unknown')
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1
        
        if type_counts:
            st.subheader("📈 Conflict Types Distribution")
            
            # Create DataFrame for chart
            df = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
            
            # Display as bar chart
            st.bar_chart(df.set_index('Type'))
    
    def render_recommendations(self, conflicts: List[Dict[str, Any]]):
        """Render recommendations based on detected conflicts."""
        if not conflicts:
            return
        
        st.subheader("💡 Recommendations")
        
        # Generate recommendations based on conflict types
        recommendations = self._generate_recommendations(conflicts)
        
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    
    def _generate_recommendations(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on conflicts."""
        recommendations = []
        conflict_types = [c.get('type', '').lower() for c in conflicts]
        
        if any('pricing' in ct for ct in conflict_types):
            recommendations.append("Review pricing structures across all documents to ensure consistency")
        
        if any('term' in ct for ct in conflict_types):
            recommendations.append("Standardize contract terms and conditions")
        
        if any('date' in ct or 'deadline' in ct for ct in conflict_types):
            recommendations.append("Verify all dates and deadlines for accuracy")
        
        if any('contact' in ct or 'information' in ct for ct in conflict_types):
            recommendations.append("Update contact information to match latest records")
        
        if len(conflicts) > 5:
            recommendations.append("Consider consolidating documents to reduce conflicts")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Review all highlighted conflicts and resolve inconsistencies")
        
        return recommendations
    
    def render_export_options(self, conflicts: List[Dict[str, Any]]):
        """Render export options for conflicts."""
        if not conflicts:
            return
        
        st.subheader("📤 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Copy to Clipboard"):
                # Generate text summary
                summary = self._generate_text_summary(conflicts)
                st.code(summary)
                st.success("Summary generated! Copy the text above.")
        
        with col2:
            if st.button("📊 Download Report"):
                # Generate downloadable report
                report_data = self._generate_report_data(conflicts)
                st.download_button(
                    label="Download CSV Report",
                    data=report_data,
                    file_name=f"conflict_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    def _generate_text_summary(self, conflicts: List[Dict[str, Any]]) -> str:
        """Generate a text summary of conflicts."""
        summary = f"CONFLICT ANALYSIS REPORT\n"
        summary += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"Total Conflicts: {len(conflicts)}\n\n"
        
        for i, conflict in enumerate(conflicts, 1):
            summary += f"CONFLICT #{i}\n"
            summary += f"Type: {conflict.get('type', 'Unknown')}\n"
            summary += f"Severity: {conflict.get('severity', 'Medium')}\n"
            summary += f"Description: {conflict.get('description', 'N/A')}\n"
            if conflict.get('details'):
                summary += f"Details: {conflict['details']}\n"
            summary += "\n"
        
        return summary
    
    def _generate_report_data(self, conflicts: List[Dict[str, Any]]) -> str:
        """Generate CSV report data."""
        # Convert conflicts to DataFrame
        df_data = []
        for i, conflict in enumerate(conflicts, 1):
            df_data.append({
                'Conflict_ID': i,
                'Type': conflict.get('type', 'Unknown'),
                'Severity': conflict.get('severity', 'Medium'),
                'Description': conflict.get('description', ''),
                'Confidence': conflict.get('confidence', ''),
                'Source_Documents': ', '.join(conflict.get('source_documents', []))
            })
        
        df = pd.DataFrame(df_data)
        return df.to_csv(index=False)
