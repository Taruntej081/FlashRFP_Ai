import time
import unittest
from roi_tracker import init_roi_tracker, log_ai_performance, calculate_roi

def test_roi_suite():
    print("--- Testing ROI & Time Monitoring Engine ---")
    
    # Mock Streamlit session state
    class SessionState(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value

    import streamlit as st
    st.session_state = SessionState()

    init_roi_tracker()
    
    # Simulate single question (takes 1.5s AI time)
    log_ai_performance(100.0, 101.5, "question", quantity=1)
    
    # Simulate batch 10 questions (takes 5.0s AI time)
    log_ai_performance(200.0, 205.0, "question", quantity=10)
    
    # Simulate BOQ excel 25 rows (takes 8.0s AI time)
    log_ai_performance(300.0, 308.0, "boq", quantity=25)
    
    roi = calculate_roi()
    print("ROI Calculated Metrics:")
    print(roi)
    
    assert roi["questions"] == 11, f"Expected 11 questions, got {roi['questions']}"
    assert roi["boq_rows"] == 25, f"Expected 25 BOQ rows, got {roi['boq_rows']}"
    assert roi["human_minutes_saved"] == (11 * 30) + (25 * 2), "Human minutes saved calculation mismatch!"
    assert roi["cost_saved"] == (roi["human_hours_saved"] * 500), "Financial cost saved calculation mismatch!"
    assert roi["human_formatted"] == "6h 20m", f"Expected '6h 20m', got {roi['human_formatted']}"
    assert roi["ai_formatted"] == "14.5s", f"Expected '14.5s', got {roi['ai_formatted']}"
    assert roi["speedup"] > 10.0, "Speedup ratio calculation issue!"
    
    print("\n[PASS] ROI & Time Tracking Engine Test PASSED cleanly!")

if __name__ == "__main__":
    test_roi_suite()
