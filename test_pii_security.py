from rag_engine import mask_pii, scrub_pii, get_chroma_client, get_or_create_collection, ingest_document

def test_pii_security_suite():
    print("--- Testing Enterprise PII Data Redaction Suite ---")
    
    sample_text = """
    Enterprise Confidential Document:
    Client Name: Rajesh Kumar
    Aadhaar Number: 1234 5678 9012
    PAN Card: ABCDE1234F
    Credit Card: 4532 1122 3344 5566
    Corporate Email: rajesh.k@enterprise-tech.com
    US SSN: 123-45-6789
    Contact Phone: +91 98765 43210
    System Spec: Dual Xeon 6330, 256GB RAM
    """
    
    masked = mask_pii(sample_text)
    print("Masked Sample Output:")
    print(masked)
    
    assert "1234 5678 9012" not in masked, "Aadhaar number was not redacted!"
    assert "[AADHAAR MASKED]" in masked, "Aadhaar mask tag missing!"
    
    assert "ABCDE1234F" not in masked, "PAN card number was not redacted!"
    assert "[PAN MASKED]" in masked, "PAN mask tag missing!"
    
    assert "4532 1122 3344 5566" not in masked, "Credit card number was not redacted!"
    assert "[CREDIT CARD MASKED]" in masked, "Credit Card mask tag missing!"
    
    assert "rajesh.k@enterprise-tech.com" not in masked, "Email address was not redacted!"
    assert "[EMAIL MASKED]" in masked, "Email mask tag missing!"
    
    assert "Dual Xeon 6330" in masked, "Legitimate non-PII technical specs were wrongly altered!"
    
    print("[PASS] PII Redaction Engine Test PASSED cleanly!")

if __name__ == "__main__":
    test_pii_security_suite()
