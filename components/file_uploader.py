"""
Enhanced File Uploader Component for Streamlit
"""

import streamlit as st
from typing import List, Optional, Dict, Any
from pathlib import Path

class FileUploaderComponent:
    """Enhanced file uploader with validation and preview"""
    
    def __init__(self):
        self.supported_types = ['txt', 'pdf', 'docx', 'md', 'html']
        self.max_file_size = 50  # MB
        self.max_files = 5
    
    def render(self) -> Optional[List[Any]]:
        """
        Render the file upload interface
        
        Returns:
            List of uploaded files or None
        """
        
        st.header("📁 Document Upload")
        
        # Upload instructions
        with st.expander("ℹ️ Upload Guidelines", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Supported File Types:**")
                for file_type in self.supported_types:
                    st.write(f"• .{file_type}")
            
            with col2:
                st.write("**Limits:**")
                st.write(f"• Max file size: {self.max_file_size} MB")
                st.write(f"• Max files: {self.max_files}")
                st.write("• Recommended: 2-3 documents")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Select documents to analyze",
            accept_multiple_files=True,
            type=self.supported_types,
            help="Upload policy documents, contracts, guidelines, or any text documents to check for contradictions"
        )
        
        if uploaded_files:
            # Validate uploads
            valid_files, warnings = self._validate_uploads(uploaded_files)
            
            # Show warnings if any
            for warning in warnings:
                st.warning(warning)
            
            if valid_files:
                # Show upload success
                st.success(f"✅ {len(valid_files)} files uploaded successfully")
                
                # Render file preview
                self._render_file_preview(valid_files)
                
                return valid_files
            else:
                st.error("❌ No valid files uploaded. Please check file requirements.")
                return None
        
        else:
            # Show upload prompt
            st.info("👆 Upload 2-3 documents to get started with conflict analysis")
            return None
    
    def _validate_uploads(self, uploaded_files: List[Any]) -> tuple[List[Any], List[str]]:
        """
        Validate uploaded files
        
        Returns:
            Tuple of (valid_files, warnings)
        """
        
        valid_files = []
        warnings = []
        
        # Check file count
        if len(uploaded_files) > self.max_files:
            warnings.append(f"⚠️ Too many files. Only processing first {self.max_files} files.")
            uploaded_files = uploaded_files[:self.max_files]
        
        # Validate each file
        for uploaded_file in uploaded_files:
            # Check file size
            if uploaded_file.size > self.max_file_size * 1024 * 1024:
                warnings.append(f"⚠️ {uploaded_file.name} exceeds size limit ({self.max_file_size}MB)")
                continue
            
            # Check file type
            file_extension = Path(uploaded_file.name).suffix.lower().lstrip('.')
            if file_extension not in self.supported_types:
                warnings.append(f"⚠️ {uploaded_file.name} has unsupported file type (.{file_extension})")
                continue
            
            # Check if file has content
            if uploaded_file.size == 0:
                warnings.append(f"⚠️ {uploaded_file.name} is empty")
                continue
            
            valid_files.append(uploaded_file)
        
        return valid_files, warnings
    
    def _render_file_preview(self, uploaded_files: List[Any]):
        """Render preview of uploaded files"""
        
        # File summary
        total_size = sum(file.size for file in uploaded_files)
        total_size_mb = total_size / (1024 * 1024)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Files", len(uploaded_files))
        with col2:
            st.metric("Total Size", f"{total_size_mb:.1f} MB")
        with col3:
            file_types = set(Path(f.name).suffix.lower() for f in uploaded_files)
            st.metric("Types", len(file_types))
        
        # Individual file details
        st.subheader("📄 File Details")
        
        for i, uploaded_file in enumerate(uploaded_files):
            with st.expander(f"{i+1}. {uploaded_file.name} ({uploaded_file.size:,} bytes)"):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # File metadata
                    st.write(f"**Name:** {uploaded_file.name}")
                    st.write(f"**Type:** {uploaded_file.type}")
                    st.write(f"**Size:** {self._format_file_size(uploaded_file.size)}")
                    
                with col2:
                    # File type icon and status
                    file_ext = Path(uploaded_file.name).suffix.lower()
                    icon = self._get_file_icon(file_ext)
                    st.write(f"**File Type:** {icon} {file_ext}")
                    st.write("**Status:** ✅ Ready")
                
                # Content preview for text files
                if uploaded_file.type == "text/plain" or uploaded_file.name.endswith(('.md', '.txt')):
                    try:
                        # Reset file pointer
                        uploaded_file.seek(0)
                        content = uploaded_file.read().decode('utf-8', errors='ignore')
                        
                        if len(content) > 0:
                            preview_length = min(300, len(content))
                            preview = content[:preview_length]
                            
                            st.text_area(
                                "Content Preview:",
                                value=preview + ("..." if len(content) > preview_length else ""),
                                height=100,
                                disabled=True
                            )
                            
                            # Word count
                            word_count = len(content.split())
                            st.write(f"**Word Count:** {word_count:,} words")
                        
                        # Reset file pointer for processing
                        uploaded_file.seek(0)
                        
                    except Exception as e:
                        st.warning(f"Could not preview file: {str(e)}")
                
                elif uploaded_file.type == "application/pdf":
                    st.info("📄 PDF file - content will be extracted during analysis")
                
                elif "word" in uploaded_file.type.lower() or uploaded_file.name.endswith('.docx'):
                    st.info("📝 Word document - content will be extracted during analysis")
                
                else:
                    st.info("📋 Document ready for processing")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _get_file_icon(self, file_extension: str) -> str:
        """Get emoji icon for file type"""
        
        icons = {
            '.txt': '📄',
            '.md': '📝',
            '.pdf': '📕',
            '.docx': '📘',
            '.doc': '📘',
            '.html': '🌐',
            '.xml': '🗂️'
        }
        
        return icons.get(file_extension, '📋')
    
    def render_upload_tips(self):
        """Render tips for better document upload"""
        
        with st.sidebar:
            st.subheader("📚 Upload Tips")
            
            tips = [
                "Upload related documents (e.g., policies from same organization)",
                "Include documents that might have overlapping content",
                "Text-based formats work best for analysis",
                "Ensure documents are in English for optimal results",
                "Remove sensitive information before uploading"
            ]
            
            for tip in tips:
                st.write(f"💡 {tip}")
    
    def get_upload_stats(self, uploaded_files: List[Any]) -> Dict[str, Any]:
        """Get statistics about uploaded files"""
        
        if not uploaded_files:
            return {}
        
        total_size = sum(file.size for file in uploaded_files)
        file_types = {}
        
        for file in uploaded_files:
            file_type = Path(file.name).suffix.lower()
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            'total_files': len(uploaded_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'file_types': file_types,
            'largest_file': max(uploaded_files, key=lambda x: x.size).name,
            'smallest_file': min(uploaded_files, key=lambda x: x.size).name
        }