"""
Flexprice Client Module
Handles usage tracking and billing integration
"""
import requests
import streamlit as st
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from config.settings import AppSettings

class FlexpriceClient:
    """Client for Flexprice usage-based billing API"""
    
    def __init__(self):
        self.settings = AppSettings()
        self.config = self.settings.get_flexprice_config()
        self.api_key = self.config.get("api_key", "")
        self.base_url = self.config.get("base_url", "https://api.flexprice.com/v1")
        self.session_id = str(uuid.uuid4())
        
        # Initialize usage tracking
        self._initialize_usage_tracking()
    
    def _initialize_usage_tracking(self):
        """Initialize usage tracking in session state"""
        if not hasattr(st.session_state, 'flexprice_events'):
            st.session_state.flexprice_events = []
        if not hasattr(st.session_state, 'billing_session'):
            st.session_state.billing_session = {
                'session_id': self.session_id,
                'start_time': datetime.now(timezone.utc).isoformat(),
                'customer_id': self._get_customer_id(),
                'total_amount': 0.0
            }
        if not hasattr(st.session_state, 'customer_id'):
            st.session_state.customer_id = f"demo_user_{uuid.uuid4().hex[:8]}"
    
    def _get_customer_id(self) -> str:
        """Get or generate customer ID"""
        # In production, this would come from user authentication
        if 'customer_id' not in st.session_state:
            st.session_state.customer_id = f"demo_user_{uuid.uuid4().hex[:8]}"
        return st.session_state.customer_id
    
    def track_document_analysis(self, doc_count: int, metadata: Optional[Dict] = None) -> float:
        """
        Track document analysis usage
        
        Args:
            doc_count: Number of documents analyzed
            metadata: Additional metadata (file types, sizes, etc.)
            
        Returns:
            Cost of the analysis
        """
        
        cost_per_doc = self.settings.PRICING["document_analysis"]
        total_cost = doc_count * cost_per_doc
        
        event_data = {
            "event_type": "document_analysis",
            "quantity": doc_count,
            "unit_price": cost_per_doc,
            "total_amount": total_cost,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "customer_id": self._get_customer_id()
        }
        
        # Track the event
        success = self._send_usage_event(event_data)
        
        if success:
            # Update session totals
            st.session_state.billing_session['total_amount'] += total_cost
            st.session_state.flexprice_events.append(event_data)
        
        return total_cost
    
    def track_report_generation(self, report_type: str = "standard", metadata: Optional[Dict] = None) -> float:
        """
        Track report generation usage
        
        Args:
            report_type: Type of report generated
            metadata: Additional metadata (conflict count, etc.)
            
        Returns:
            Cost of report generation
        """
        
        cost = self.settings.PRICING["report_generation"]
        
        if report_type == "premium":
            cost = self.settings.PRICING["premium_analysis"]
        
        event_data = {
            "event_type": "report_generation",
            "quantity": 1,
            "unit_price": cost,
            "total_amount": cost,
            "metadata": {
                "report_type": report_type,
                **(metadata or {})
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "customer_id": self._get_customer_id()
        }
        
        # Track the event
        success = self._send_usage_event(event_data)
        
        if success:
            # Update session totals
            st.session_state.billing_session['total_amount'] += cost
            st.session_state.flexprice_events.append(event_data)
        
        return cost
    
    def track_llm_usage(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Track LLM API usage costs
        
        Args:
            model_name: Name of the LLM model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost of LLM usage
        """
        
        model_config = self.settings.get_model_config(model_name)
        
        input_cost = input_tokens * model_config.get("cost_per_input_token", 0)
        output_cost = output_tokens * model_config.get("cost_per_output_token", 0)
        total_cost = input_cost + output_cost
        
        event_data = {
            "event_type": "llm_usage",
            "quantity": 1,
            "unit_price": total_cost,
            "total_amount": total_cost,
            "metadata": {
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_cost": input_cost,
                "output_cost": output_cost
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "customer_id": self._get_customer_id()
        }
        
        # Track the event (internal tracking only, not billed to customer)
        st.session_state.flexprice_events.append(event_data)
        
        return total_cost
    
    def _send_usage_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Send usage event to Flexprice API
        
        Args:
            event_data: Usage event data
            
        Returns:
            True if successful, False otherwise
        """
        
        if not self.api_key:
            # Mock mode - just log the event
            self._log_mock_event(event_data)
            return True
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/usage",
                headers=headers,
                json=event_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                st.warning(f"Billing API error: {response.status_code}")
                self._log_mock_event(event_data)  # Fallback to local logging
                return False
                
        except requests.exceptions.RequestException as e:
            st.warning(f"Billing API unavailable: {str(e)}")
            self._log_mock_event(event_data)  # Fallback to local logging
            return False
    
    def _log_mock_event(self, event_data: Dict[str, Any]):
        """Log event locally when API is unavailable"""
        if self.settings.DEBUG:
            st.write("**Mock Billing Event:**", event_data)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current session usage summary"""
        
        # Initialize if not exists
        if not hasattr(st.session_state, 'flexprice_events'):
            st.session_state.flexprice_events = []
        
        if not st.session_state.flexprice_events:
            return {
                "total_events": 0,
                "total_amount": 0.0,
                "events_by_type": {},
                "session_duration": "0 minutes"
            }
        
        events = st.session_state.flexprice_events
        
        # Calculate totals
        total_amount = sum(event.get("total_amount", 0) for event in events)
        
        # Group by event type
        events_by_type = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            if event_type not in events_by_type:
                events_by_type[event_type] = {
                    "count": 0,
                    "total_amount": 0.0
                }
            events_by_type[event_type]["count"] += 1
            events_by_type[event_type]["total_amount"] += event.get("total_amount", 0)
        
        # Calculate session duration
        start_time = datetime.fromisoformat(st.session_state.billing_session['start_time'].replace('Z', '+00:00'))
        duration = datetime.now(timezone.utc) - start_time
        duration_minutes = int(duration.total_seconds() / 60)
        
        return {
            "total_events": len(events),
            "total_amount": total_amount,
            "events_by_type": events_by_type,
            "session_duration": f"{duration_minutes} minutes",
            "customer_id": self._get_customer_id(),
            "session_id": self.session_id
        }
    
    def get_detailed_usage(self) -> List[Dict[str, Any]]:
        """Get detailed usage events for the current session"""
        return st.session_state.flexprice_events.copy()
    
    def get_usage_events(self) -> List[Dict[str, Any]]:
        """Get usage events for timeline visualization"""
        # Initialize if not exists
        if not hasattr(st.session_state, 'flexprice_events'):
            st.session_state.flexprice_events = []
        
        return st.session_state.flexprice_events.copy()
    
    def export_usage_data(self) -> str:
        """Export usage data as JSON string"""
        
        export_data = {
            "session_info": st.session_state.billing_session,
            "usage_events": st.session_state.flexprice_events,
            "summary": self.get_usage_summary(),
            "export_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def reset_session(self):
        """Reset the current billing session"""
        
        # Clear session state
        st.session_state.flexprice_events = []
        self.session_id = str(uuid.uuid4())
        st.session_state.billing_session = {
            'session_id': self.session_id,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'customer_id': self._get_customer_id(),
            'total_amount': 0.0
        }
    
    def validate_api_connection(self) -> Dict[str, Any]:
        """Validate connection to Flexprice API"""
        
        if not self.api_key:
            return {
                "status": "mock",
                "message": "Running in mock mode - no API key configured",
                "connected": False
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test API connection with a ping endpoint
            response = requests.get(
                f"{self.base_url}/ping",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "message": "Successfully connected to Flexprice API",
                    "connected": True
                }
            else:
                return {
                    "status": "error",
                    "message": f"API returned status {response.status_code}",
                    "connected": False
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "connected": False
            }
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Get current pricing information"""
        
        return {
            "pricing_model": "pay-per-use",
            "currency": "USD",
            "rates": self.settings.PRICING,
            "billing_frequency": "real-time",
            "minimum_charge": 0.01
        }
    
    def calculate_estimated_cost(self, doc_count: int, generate_report: bool = True) -> Dict[str, float]:
        """Calculate estimated cost for an analysis"""
        
        analysis_cost = doc_count * self.settings.PRICING["document_analysis"]
        report_cost = self.settings.PRICING["report_generation"] if generate_report else 0.0
        total_cost = analysis_cost + report_cost
        
        return {
            "document_analysis": analysis_cost,
            "report_generation": report_cost,
            "total_estimated": total_cost
        }


class BillingDashboard:
    """Helper class for rendering billing dashboard in Streamlit"""
    
    def __init__(self, flexprice_client: FlexpriceClient):
        self.client = flexprice_client
    
    def render_usage_metrics(self):
        """Render usage metrics in Streamlit"""
        
        usage_summary = self.client.get_usage_summary()
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Events", usage_summary["total_events"])
        
        with col2:
            st.metric("Session Cost", f"${usage_summary['total_amount']:.2f}")
        
        with col3:
            st.metric("Duration", usage_summary["session_duration"])
        
        with col4:
            api_status = self.client.validate_api_connection()
            status_color = "🟢" if api_status["connected"] else "🟡" if api_status["status"] == "mock" else "🔴"
            st.metric("API Status", f"{status_color} {api_status['status'].title()}")
        
        # Events breakdown
        if usage_summary["events_by_type"]:
            st.subheader("Usage Breakdown")
            
            for event_type, data in usage_summary["events_by_type"].items():
                with st.expander(f"{event_type.replace('_', ' ').title()} - {data['count']} events"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Events", data["count"])
                    with col2:
                        st.metric("Cost", f"${data['total_amount']:.2f}")
    
    def render_pricing_table(self):
        """Render pricing information table"""
        
        pricing_info = self.client.get_pricing_info()
        
        st.subheader("💰 Pricing Information")
        
        pricing_data = []
        for service, price in pricing_info["rates"].items():
            pricing_data.append({
                "Service": service.replace('_', ' ').title(),
                "Price": f"${price:.2f}",
                "Unit": "per document" if "document" in service else "per report" if "report" in service else "per analysis"
            })
        
        st.table(pricing_data)
    
    def render_cost_estimator(self):
        """Render cost estimation tool"""
        
        st.subheader("📊 Cost Estimator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            doc_count = st.number_input("Number of Documents", min_value=1, max_value=10, value=3)
        
        with col2:
            generate_report = st.checkbox("Generate Report", value=True)
        
        if st.button("Calculate Cost"):
            estimate = self.client.calculate_estimated_cost(doc_count, generate_report)
            
            st.success("**Cost Breakdown:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Analysis", f"${estimate['document_analysis']:.2f}")
            with col2:
                st.metric("Report", f"${estimate['report_generation']:.2f}")
            with col3:
                st.metric("Total", f"${estimate['total_estimated']:.2f}")
    
    def render_usage_export(self):
        """Render usage data export functionality"""
        
        if st.button("📥 Export Usage Data"):
            usage_data = self.client.export_usage_data()
            
            st.download_button(
                label="Download Usage Report",
                data=usage_data,
                file_name=f"usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("Usage data prepared for download!")
    
    def render_session_controls(self):
        """Render session control buttons"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reset Session"):
                self.client.reset_session()
                st.success("Billing session reset!")
                st.rerun()
        
        with col2:
            if st.button("🔍 Validate API"):
                status = self.client.validate_api_connection()
                if status["connected"]:
                    st.success(status["message"])
                else:
                    st.warning(status["message"])


url = "https://api.cloud.flexprice.io/v1/secrets/api/keys"

payload = {
    "name": "ctrl+hack+win",
    "type": "integration"
}
headers = {
    "x-api-key": "<sk_01K65A8E8BWSR33Q95PB4XGMJS>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())



                  