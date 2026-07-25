import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from rag_engine import get_chroma_client, get_or_create_collection
from copilot import stream_copilot_response

def test_copilot():
    print("--- Testing FlashRFP Copilot Engine ---")
    
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    
    query = "What are the SLA resolution commitments for high severity outages?"
    chat_history = [
        {"role": "user", "content": "Tell me about your technical support policy."},
        {"role": "assistant", "content": "We offer 24/7 Enterprise Tier Support with 15-minute response times."}
    ]
    
    generator = stream_copilot_response(
        query,
        chat_history,
        collection,
        api_key="demo_key",
        tenant_id="test_tenant",
        demo_mode=True
    )
    
    response_words = list(generator)
    full_response = "".join(response_words)
    
    print("Generated Copilot Streamed Response:")
    print(" ", full_response)
    
    assert len(full_response) > 0, "Copilot response is empty!"
    assert "Based on your Knowledge Base" in full_response or "SLA" in full_response, "Unexpected Copilot output format!"
    
    print("\n[PASS] FlashRFP Copilot Engine Test PASSED cleanly!")

if __name__ == "__main__":
    test_copilot()
