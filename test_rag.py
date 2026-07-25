
import os
import sys
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from rag_engine import chunk_text, extract_text_from_pdf, extract_text_from_docx

def run_test():
    load_dotenv()
    print("=== AutoRFP AI CLI Integration Test ===")
    
    # 1. Test Text Chunker
    sample_text = (
        "AutoRFP AI is an automated bid response engine designed for B2B sales teams. "
        "It cuts proposal writing times by 90%.\n\n"
        "The system uses a vector database to search historical proposal questions and answers, "
        "then synthesizes a draft response with Google Gemini."
    )
    chunks = chunk_text(sample_text, chunk_size=150, chunk_overlap=30)
    print(f"\n[1] Chunking Test: Split text into {len(chunks)} chunks.")
    for idx, c in enumerate(chunks):
        print(f"  Chunk {idx+1} ({len(c)} chars): {repr(c)}")
        
    if len(chunks) < 2:
        print("  FAIL: Text was not chunked properly.")
        sys.exit(1)
    else:
        print("  SUCCESS: Chunking works.")

    # 2. Check API Keys
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[2] Gemini API Connection: SKIPPED (GEMINI_API_KEY is empty in .env)")
        print("  To run full vector database and LLM generation tests, please fill in your GEMINI_API_KEY in the .env file.")
        print("\nAll offline tests passed successfully!")
        return
        
    print("\n[2] Gemini API Connection: Detected key. Initializing ChromaDB test...")
    try:
        from rag_engine import get_chroma_client, get_or_create_collection, query_knowledge_base, generate_rfp_response
        
        # Initialize clients
        client = get_chroma_client(db_path="test_chroma_db")
        collection = get_or_create_collection(client, api_key, collection_name="test_rfp_kb")
        
        # Index sample chunks
        ids = ["test_chunk_1", "test_chunk_2"]
        docs = [
            "We offer a 99.9% uptime SLA for all enterprise subscription plans, backed by redundant cloud hosting.",
            "Our data security program is SOC 2 Type II certified and complies fully with GDPR and CCPA regulations."
        ]
        metadatas = [
            {"source": "sla_terms.docx", "chunk_idx": 0},
            {"source": "security_whitepaper.pdf", "chunk_idx": 0}
        ]
        
        print("  Indexing test data into ChromaDB...")
        collection.add(ids=ids, documents=docs, metadatas=metadatas)
        print("  Data indexed successfully.")
        
        # Test Query
        query = "What is your uptime SLA and how secure is your data?"
        print(f"  Querying database for: '{query}'")
        contexts = query_knowledge_base(query, collection, top_k=2)
        print(f"  Retrieved {len(contexts)} relevant contexts:")
        for ctx in contexts:
            print(f"    - Source: {ctx['source']} | Score: {ctx['similarity']}")
            print(f"      Snippet: {repr(ctx['text'])}")
            
        # Test Response Generation
        print("  Calling Gemini API to generate answer...")
        response = generate_rfp_response(api_key, query, contexts)
        print("\n--- GENERATED ANSWER ---")
        print(response)
        print("------------------------")
        
        # Test Docx Export
        from exporter import generate_docx_stream
        print("\nTesting Word Doc export...")
        docx_bytes = generate_docx_stream(query, response, contexts)
        print(f"  Word document generated successfully ({len(docx_bytes)} bytes).")
        
        # Clean up database files
        import shutil
        print("\nCleaning up test ChromaDB directory...")
        client.delete_collection("test_rfp_kb")
        # Close client connection if possible or wait for process end
        del client
        shutil.rmtree("test_chroma_db", ignore_errors=True)
        print("  SUCCESS: Integration test completed successfully!")
        
    except Exception as e:
        print(f"  FAIL: Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_test()
