"""
LLM Analyzer Module
Integrates with various LLM APIs for document conflict analysis
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
import asyncio

# LLM imports
try:
    import google.generativeai as genai
    # import openai  # Optional
except ImportError as e:
    st.error(f"Missing LLM dependencies: {e}")

from config.settings import AppSettings

class LLMDocumentAnalyzer:
    """Core LLM analyzer for document conflicts"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.settings = AppSettings()
        self.model_name = model_name
        self.model_config = self.settings.get_model_config(model_name)
        self.setup_model()
    
    def setup_model(self):
        """Setup the selected LLM model"""
        
        if self.model_name.startswith("gemini"):
            self._setup_gemini()
        elif self.model_name.startswith("grok"):
            self._setup_grok()
        else:
            st.error(f"Unsupported model: {self.model_name}")
    
    def _setup_gemini(self):
        """Configure Gemini API"""
        api_key = self.model_config.get("api_key")
        if not api_key:
            st.error("Gemini API key not found in configuration")
            return
        
        genai.configure(api_key=api_key)
        
        # Configure generation parameters
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Low temperature for consistent analysis
            top_p=0.8,
            top_k=40,
            max_output_tokens=4000,
        )
        
        # Initialize model
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            st.error(f"Failed to initialize Gemini model: {str(e)}")
            self.model = None
    
    def _setup_grok(self):
        """Configure Grok API (placeholder for future implementation)"""
        st.warning("Grok integration coming soon!")
        self.model = None
    
    def analyze_documents_for_conflicts(
        self, 
        documents: List[Dict], 
        analysis_type: str = "comprehensive"
    ) -> List[Dict]:
        """
        Main analysis function - detects conflicts using LLM
        
        Args:
            documents: List of document dictionaries with content
            analysis_type: "quick" or "comprehensive"
            
        Returns:
            List of conflict dictionaries
        """
        
        if not self.model:
            return self._fallback_analysis(documents)
        
        try:
            # Prepare analysis prompt
            system_prompt = self._get_system_prompt(analysis_type)
            user_prompt = self._create_analysis_prompt(documents)
            
            # Generate analysis
            if self.model_name.startswith("gemini"):
                response = self.model.generate_content(
                    [system_prompt, user_prompt],
                    generation_config=self.generation_config
                )
                
                # Parse LLM response
                conflicts = self._parse_gemini_response(response.text, documents)
                
            else:
                conflicts = self._fallback_analysis(documents)
            
            # Post-process and validate conflicts
            validated_conflicts = self._validate_conflicts(conflicts, documents)
            
            return validated_conflicts
            
        except Exception as e:
            st.error(f"LLM Analysis failed: {str(e)}")
            return self._fallback_analysis(documents)
    
    def _get_system_prompt(self, analysis_type: str) -> str:
        """Generate system prompt based on analysis type"""
        
        base_prompt = """
You are an expert document analyst specializing in identifying contradictions and conflicts across organizational documents. Your expertise includes:

- Policy analysis and compliance checking
- Legal document review for inconsistencies  
- Academic regulation analysis
- Corporate procedure validation

ANALYSIS FRAMEWORK:
1. IDENTIFY CONFLICTS: Find direct contradictions between documents
2. CATEGORIZE TYPES: Deadline conflicts, policy contradictions, requirement mismatches
3. ASSESS IMPACT: Rate severity as High, Medium, or Low based on operational impact
4. PROVIDE EVIDENCE: Quote specific conflicting text passages
5. SUGGEST RESOLUTION: Offer concrete, actionable recommendations
6. CONFIDENCE SCORING: Rate confidence in detection (0.0-1.0)

CONFLICT TYPES TO DETECT:
- Temporal conflicts (deadlines, dates, timeframes)
- Quantitative conflicts (percentages, amounts, limits)
- Procedural conflicts (different steps for same process)
- Authority conflicts (conflicting responsibilities)
- Policy contradictions (opposing rules or guidelines)

SEVERITY GUIDELINES:
- HIGH: Conflicts causing operational confusion, legal issues, or compliance problems
- MEDIUM: Conflicts causing minor confusion but manageable
- LOW: Potential inconsistencies that may cause future issues

OUTPUT FORMAT: Provide structured analysis with specific examples and actionable recommendations.
"""
        
        if analysis_type == "quick":
            return base_prompt + "\n\nFOCUS: Prioritize obvious, high-impact conflicts only. Be concise."
        else:
            return base_prompt + "\n\nFOCUS: Comprehensive analysis including subtle conflicts and edge cases."
    
    def _create_analysis_prompt(self, documents: List[Dict]) -> str:
        """Create the analysis prompt with document content"""
        
        # Format documents for analysis
        doc_sections = []
        
        for i, doc in enumerate(documents, 1):
            content = doc['content']
            
            # Truncate very long documents to fit context window
            max_chars = 8000 if len(documents) > 2 else 12000
            if len(content) > max_chars:
                content = content[:max_chars] + "\n[DOCUMENT TRUNCATED]"
            
            doc_section = f"""
=== DOCUMENT {i}: {doc['name']} ===
Type: {doc.get('file_type', 'Unknown')}
Size: {doc.get('word_count', 0)} words
Content:
{content}

========================

"""
            doc_sections.append(doc_section)
        
        # Create the full prompt
        prompt = f"""
TASK: Analyze the following {len(documents)} documents for contradictions, conflicts, and inconsistencies.

DOCUMENTS TO ANALYZE:
{''.join(doc_sections)}

ANALYSIS INSTRUCTIONS:
1. Compare all documents against each other systematically
2. Look for conflicts in:
   - Deadlines and time requirements
   - Policies and rules
   - Procedures and processes
   - Requirements and standards
   - Authority and responsibilities

3. For each conflict found, provide:
   - Conflict type and category
   - Severity level (High/Medium/Low)
   - Specific quotes from conflicting documents
   - Clear explanation of why it's a conflict
   - Practical resolution suggestion
   - Confidence score (0.0-1.0)

4. Focus on actionable conflicts that would cause real operational issues

Please provide a detailed analysis of all conflicts found.
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str, documents: List[Dict]) -> List[Dict]:
        """Parse Gemini's response into structured conflict data"""
        
        conflicts = []
        
        try:
            # Split response into sections
            sections = self._split_response_sections(response_text)
            
            for section in sections:
                conflict = self._extract_conflict_from_section(section, documents)
                if conflict:
                    conflicts.append(conflict)
            
            # If no structured conflicts found, try alternative parsing
            if not conflicts:
                conflicts = self._fallback_parse(response_text, documents)
                
        except Exception as e:
            st.error(f"Error parsing LLM response: {str(e)}")
            conflicts = self._create_summary_conflict(response_text, documents)
        
        return conflicts[:10]  # Limit to top 10 most important conflicts
    
    def _split_response_sections(self, text: str) -> List[str]:
        """Split response into conflict sections"""
        
        # Try to identify conflict sections
        conflict_markers = [
            r'(?i)conflict\s*\d*[:\-]',
            r'(?i)contradiction\s*\d*[:\-]',
            r'(?i)inconsistency\s*\d*[:\-]',
            r'(?i)issue\s*\d*[:\-]'
        ]
        
        sections = []
        
        # Split by common section markers
        for marker in conflict_markers:
            potential_sections = re.split(marker, text)
            if len(potential_sections) > len(sections):
                sections = potential_sections
        
        # If no clear sections, split by double newlines
        if len(sections) <= 1:
            sections = text.split('\n\n')
        
        # Filter out very short sections
        sections = [s.strip() for s in sections if len(s.strip()) > 50]
        
        return sections
    
    def _extract_conflict_from_section(self, section: str, documents: List[Dict]) -> Optional[Dict]:
        """Extract conflict details from a text section"""
        
        if len(section) < 50:  # Skip very short sections
            return None
        
        # Extract severity
        severity = self._extract_severity(section)
        
        # Extract confidence score
        confidence = self._extract_confidence(section)
        
        # Determine conflict type
        conflict_type = self._classify_conflict_type(section)
        
        # Extract description (first meaningful sentence)
        description = self._extract_description(section)
        
        # Find affected documents
        affected_docs = self._find_affected_documents(section, documents)
        
        # Generate suggestion
        suggestion = self._generate_suggestion(section, conflict_type)
        
        return {
            'type': conflict_type,
            'severity': severity,
            'description': description,
            'documents': affected_docs,
            'suggestion': suggestion,
            'confidence': confidence,
            'llm_analysis': section[:500],  # Store excerpt of full analysis
            'quotes': self._extract_quotes(section)
        }
    
    def _extract_severity(self, text: str) -> str:
        """Extract severity level from text"""
        
        text_lower = text.lower()
        
        high_indicators = ['critical', 'urgent', 'serious', 'major', 'high', 'severe']
        low_indicators = ['minor', 'low', 'small', 'slight', 'trivial']
        
        if any(indicator in text_lower for indicator in high_indicators):
            return 'High'
        elif any(indicator in text_lower for indicator in low_indicators):
            return 'Low'
        else:
            return 'Medium'
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text"""
        
        # Look for percentage or decimal confidence scores
        confidence_patterns = [
            r'confidence[:\s]*(\d+(?:\.\d+)?)[%]?',
            r'certain[ty]*[:\s]*(\d+(?:\.\d+)?)[%]?',
            r'score[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                return min(score / 100 if score > 1 else score, 1.0)
        
        # Default confidence based on text analysis
        if any(word in text.lower() for word in ['clearly', 'obviously', 'definitely']):
            return 0.9
        elif any(word in text.lower() for word in ['might', 'possibly', 'potentially']):
            return 0.6
        else:
            return 0.75
    
    def _classify_conflict_type(self, text: str) -> str:
        """Classify the type of conflict"""
        
        text_lower = text.lower()
        
        type_keywords = {
            'Deadline Conflict': ['deadline', 'due date', 'time', 'schedule', 'submission'],
            'Policy Conflict': ['policy', 'rule', 'regulation', 'guideline', 'procedure'],
            'Requirement Mismatch': ['requirement', 'standard', 'criteria', 'threshold'],
            'Attendance Policy': ['attendance', 'presence', 'participation'],
            'Grading Conflict': ['grade', 'grading', 'assessment', 'evaluation'],
            'Authority Conflict': ['responsibility', 'authority', 'jurisdiction', 'oversight']
        }
        
        for conflict_type, keywords in type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return conflict_type
        
        return 'General Conflict'
    
    def _extract_description(self, text: str) -> str:
        """Extract a clear description of the conflict"""
        
        # Get first 2-3 sentences that contain substantive information
        sentences = text.split('.')
        description_parts = []
        
        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(word in sentence.lower() for word in 
                                        ['conflict', 'contradiction', 'different', 'disagree', 'inconsistent']):
                description_parts.append(sentence)
                if len(' '.join(description_parts)) > 150:
                    break
        
        description = '. '.join(description_parts)
        
        # Fallback to first 200 characters if no good description found
        if not description:
            description = text[:200].strip()
        
        return description + '.' if not description.endswith('.') else description
    
    def _find_affected_documents(self, text: str, documents: List[Dict]) -> List[str]:
        """Find which documents are referenced in the conflict"""
        
        affected = []
        
        # Look for document references
        for doc in documents:
            doc_name = doc['name']
            doc_name_base = doc_name.split('.')[0]  # Remove extension
            
            if (doc_name.lower() in text.lower() or 
                doc_name_base.lower() in text.lower() or
                f"document {documents.index(doc) + 1}" in text.lower()):
                affected.append(doc_name)
        
        # If no specific documents found, assume all documents are involved
        if not affected:
            affected = [doc['name'] for doc in documents[:2]]  # First 2 docs
        
        return affected
    
    def _generate_suggestion(self, text: str, conflict_type: str) -> str:
        """Generate a resolution suggestion"""
        
        # Common suggestion templates
        suggestions = {
            'Deadline Conflict': 'Establish a single, consistent deadline across all relevant documents',
            'Policy Conflict': 'Harmonize policies to ensure consistent application across the organization',
            'Requirement Mismatch': 'Standardize requirements to eliminate confusion and ensure compliance',
            'Attendance Policy': 'Implement uniform attendance requirements across all policies',
            'Grading Conflict': 'Align grading criteria and standards across all assessment documents',
            'Authority Conflict': 'Clarify roles and responsibilities to eliminate jurisdictional conflicts'
        }
        
        base_suggestion = suggestions.get(conflict_type, 'Review and resolve the identified inconsistency')
        
        # Try to make it more specific based on text content
        if 'percentage' in text.lower() or '%' in text:
            base_suggestion += ' and specify exact percentage thresholds'
        elif 'time' in text.lower() or 'deadline' in text.lower():
            base_suggestion += ' and specify exact dates and times'
        
        return base_suggestion
    
    def _extract_quotes(self, text: str) -> List[str]:
        """Extract quoted text from the analysis"""
        
        quotes = []
        
        # Look for quoted text in various formats
        quote_patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'states[:\s]*"([^"]+)"',
            r'says[:\s]*"([^"]+)"'
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, text)
            quotes.extend(matches)
        
        # Clean and limit quotes
        quotes = [q.strip() for q in quotes if len(q.strip()) > 10][:3]
        
        return quotes
    
    def _fallback_parse(self, response_text: str, documents: List[Dict]) -> List[Dict]:
        """Fallback parsing when structured parsing fails"""
        
        # Simple conflict detection based on key phrases
        conflict_phrases = [
            'contradict', 'conflict', 'inconsistent', 'disagree', 
            'different', 'oppose', 'versus', 'while', 'however', 'but'
        ]
        
        conflicts = []
        sentences = response_text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(phrase in sentence.lower() for phrase in conflict_phrases) and len(sentence) > 30:
                conflicts.append({
                    'type': 'Detected Conflict',
                    'severity': 'Medium',
                    'description': sentence,
                    'documents': [doc['name'] for doc in documents],
                    'suggestion': 'Review this potential conflict and establish consistent policy',
                    'confidence': 0.7,
                    'llm_analysis': sentence,
                    'quotes': []
                })
        
        return conflicts[:5]  # Limit to 5 conflicts
    
    def _create_summary_conflict(self, response_text: str, documents: List[Dict]) -> List[Dict]:
        """Create a summary conflict when parsing completely fails"""
        
        return [{
            'type': 'Analysis Summary',
            'severity': 'Medium',
            'description': response_text[:300] + '...' if len(response_text) > 300 else response_text,
            'documents': [doc['name'] for doc in documents],
            'suggestion': 'Review the full AI analysis for detailed insights',
            'confidence': 0.6,
            'llm_analysis': response_text,
            'quotes': []
        }]
    
    def _validate_conflicts(self, conflicts: List[Dict], documents: List[Dict]) -> List[Dict]:
        """Validate and clean up detected conflicts"""
        
        validated = []
        
        for conflict in conflicts:
            # Ensure all required fields are present
            if not all(key in conflict for key in ['type', 'severity', 'description', 'documents', 'suggestion', 'confidence']):
                continue
            
            # Validate confidence score
            conflict['confidence'] = max(0.0, min(1.0, conflict['confidence']))
            
            # Ensure description is not empty
            if not conflict['description'].strip():
                continue
            
            # Ensure documents list is not empty
            if not conflict['documents']:
                conflict['documents'] = [doc['name'] for doc in documents[:2]]
            
            validated.append(conflict)
        
        return validated
    
    def _fallback_analysis(self, documents: List[Dict]) -> List[Dict]:
        """Basic fallback analysis when LLM is unavailable"""
        
        conflicts = []
        
        # Simple keyword-based conflict detection
        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents[i+1:], i+1):
                # Check for potential conflicts
                if self._basic_conflict_check(doc1['content'], doc2['content']):
                    conflicts.append({
                        'type': 'Potential Conflict',
                        'severity': 'Medium',
                        'description': f'Potential conflicts detected between {doc1["name"]} and {doc2["name"]}',
                        'documents': [doc1['name'], doc2['name']],
                        'suggestion': 'Manual review recommended - LLM analysis unavailable',
                        'confidence': 0.5,
                        'llm_analysis': 'Basic keyword-based detection',
                        'quotes': []
                    })
        
        return conflicts
    
    def _basic_conflict_check(self, content1: str, content2: str) -> bool:
        """Basic conflict detection using keywords"""
        
        import re
        
        # Look for conflicting patterns
        time_pattern = r'\b(?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s*(?:AM|PM|am|pm)\b'
        percent_pattern = r'\b\d{1,2}%\b'
        number_pattern = r'\b\d+\b'
        
        times1 = set(re.findall(time_pattern, content1))
        times2 = set(re.findall(time_pattern, content2))
        
        percents1 = set(re.findall(percent_pattern, content1))
        percents2 = set(re.findall(percent_pattern, content2))
        
        # Check for different values
        return (times1 and times2 and not times1.intersection(times2)) or \
               (percents1 and percents2 and not percents1.intersection(percents2))


class EnhancedConflictAnalyzer:
    """Enhanced analyzer with multiple LLM support and advanced features"""
    
    def __init__(self):
        self.settings = AppSettings()
        self.current_analyzer = None
        self.supported_models = ["gemini-2.5-flash", "gemini-pro", "grok"]
    
    def analyze_documents_for_conflicts(
        self, 
        documents: List[Dict], 
        model: str = "gemini-2.5-flash",
        analysis_type: str = "comprehensive"
    ) -> List[Dict]:
        """Main analysis entry point with model selection"""
        
        # Initialize analyzer for selected model
        if not self.current_analyzer or self.current_analyzer.model_name != model:
            self.current_analyzer = LLMDocumentAnalyzer(model)
        
        return self.current_analyzer.analyze_documents_for_conflicts(documents, analysis_type)
    
    def get_analysis_summary(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive analysis summary"""
        
        if not conflicts:
            return {
                'total_conflicts': 0,
                'severity_breakdown': {'High': 0, 'Medium': 0, 'Low': 0},
                'conflict_types': {},
                'most_critical': None,
                'recommendations': ['No conflicts detected - documents appear consistent'],
                'overall_risk_level': 'Low'
            }
        
        # Calculate severity breakdown
        severity_count = {'High': 0, 'Medium': 0, 'Low': 0}
        conflict_types = {}
        confidence_scores = []
        
        for conflict in conflicts:
            severity_count[conflict['severity']] += 1
            conflict_type = conflict['type']
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
            confidence_scores.append(conflict['confidence'])
        
        # Find most critical conflict
        high_severity = [c for c in conflicts if c['severity'] == 'High']
        most_critical = high_severity[0] if high_severity else conflicts[0]
        
        # Determine overall risk level
        overall_risk = self._calculate_risk_level(severity_count, len(conflicts))
        
        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations(
            conflicts, severity_count, conflict_types
        )
        
        return {
            'total_conflicts': len(conflicts),
            'severity_breakdown': severity_count,
            'conflict_types': conflict_types,
            'most_critical': most_critical,
            'recommendations': recommendations,
            'overall_risk_level': overall_risk,
            'average_confidence': sum(confidence_scores) / len(confidence_scores),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_risk_level(self, severity_count: Dict[str, int], total_conflicts: int) -> str:
        """Calculate overall risk level"""
        
        if severity_count['High'] >= 3:
            return 'Critical'
        elif severity_count['High'] >= 1 or severity_count['Medium'] >= 5:
            return 'High'
        elif total_conflicts >= 3:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_comprehensive_recommendations(
        self, 
        conflicts: List[Dict], 
        severity_count: Dict[str, int],
        conflict_types: Dict[str, int]
    ) -> List[str]:
        """Generate comprehensive recommendations"""
        
        recommendations = []
        
        # Priority-based recommendations
        if severity_count['High'] > 0:
            recommendations.append(f"🔴 URGENT: Address {severity_count['High']} high-severity conflicts immediately")
        
        if severity_count['Medium'] > 3:
            recommendations.append(f"🟡 IMPORTANT: Schedule resolution of {severity_count['Medium']} medium-priority conflicts")
        
        # Type-specific recommendations
        if conflict_types:
            most_common_type = max(conflict_types, key=conflict_types.get)
            recommendations.append(f"📋 Focus on {most_common_type} issues - most frequent conflict type ({conflict_types[most_common_type]} instances)")
        
        # General recommendations
        recommendations.extend([
            "📝 Create a master policy document to serve as the authoritative source",
            "👥 Form a cross-functional team to review and resolve conflicts",
            "📅 Implement regular document consistency audits",
            "🔄 Establish a change management process for document updates"
        ])
        
        return recommendations[:8]  # Top 8 recommendations
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        
        return {
            "supported_models": self.supported_models,
            "current_model": self.current_analyzer.model_name if self.current_analyzer else None,
            "model_configs": {
                model: self.settings.get_model_config(model)
                for model in self.supported_models
            }
        }