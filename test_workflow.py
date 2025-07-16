#!/usr/bin/env python3
"""
Test script for the Scrum AI workflow components
This script tests the workflow logic without requiring full external service setup
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_workflow_components():
    """Test the workflow components with mocked dependencies"""
    
    print("🧪 Testing Scrum AI Workflow Components")
    print("=" * 50)
    
    # Mock the external dependencies
    with patch('agentic.utils.firebase_client.get_firestore') as mock_firestore, \
         patch('agentic.utils.pinecone_client.init_pinecone') as mock_pinecone, \
         patch('agentic.utils.model_loader.load_model') as mock_model, \
         patch('agentic.utils.text_splitter.split_project_markdown') as mock_splitter, \
         patch('agentic.utils.embedding.embed_documents') as mock_embedder:
        
        # Setup mocks
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        
        mock_index = Mock()
        mock_pinecone.return_value = mock_index
        
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = "Test response"
        mock_model.return_value = mock_llm
        
        # Mock text processing
        from langchain.schema import Document
        mock_docs = [Document(page_content="Test content")]
        mock_splitter.return_value = mock_docs
        mock_embedder.return_value = [[0.1, 0.2, 0.3]]
        
        # Test the workflow builder
        try:
            from agent.agenticworkflow import ScrumGraphBuilder
            
            # Create workflow instance
            workflow = ScrumGraphBuilder()
            graph = workflow()
            
            print("✓ Workflow builder created successfully")
            
            # Test initial state
            initial_state = {
                "project_id": "test-proj-123",
                "project_description": "Test project description for mood-based music recommender",
                "scrum_cycle": 0,
                "done": False
            }
            
            print("✓ Initial state created")
            
            # Test that the graph can be built
            if graph is not None:
                print("✓ Graph compiled successfully")
            else:
                print("✗ Graph compilation failed")
                return False
                
        except Exception as e:
            print(f"✗ Error creating workflow: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n✅ All basic workflow tests passed!")
    return True

def test_tools():
    """Test the tool functions with real Firestore (no mocking)"""
    print("\n🔧 Testing Tool Functions")
    print("=" * 30)

    try:
        from agentic.utils.firebase_client import get_firestore
        from agentic.tool.firebase_tool import write_project_summary, get_dev_profiles

        db = get_firestore()
        project_id = "test-proj"

        # --- SETUP: Create the project document if it doesn't exist ---
        project_ref = db.collection("projects").document(project_id)
        if not project_ref.get().exists:
            project_ref.set({"id": project_id, "summary": "Initial summary"})

        # --- SETUP: Create a dev_profiles subcollection with one dev ---
        dev_profiles_ref = project_ref.collection("dev_profiles").document("dev1")
        if not dev_profiles_ref.get().exists:
            dev_profiles_ref.set({
                "id": "dev1",
                "name": "Test Dev",
                "tech": ["Python"],
                "role": "Tester"
            })

        # --- TEST: write_project_summary ---
        result = write_project_summary.invoke({"project_id": project_id, "summary": "Test summary"})
        print("✓ write_project_summary tool works")

        # --- TEST: get_dev_profiles ---
        result = get_dev_profiles.invoke({"project_id": project_id})
        print("✓ get_dev_profiles tool works")
        print("Dev profiles returned:", result)

    except Exception as e:
        print(f"✗ Error testing tools: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("✅ All tool tests passed!")
    return True

def test_utilities():
    """Test utility functions"""
    
    print("\n🛠️ Testing Utility Functions")
    print("=" * 30)
    
    try:
        # Test text splitter
        from agentic.utils.text_splitter import split_project_markdown
        
        test_text = """# Project Title
        ## Section 1
        This is some content.
        ## Section 2
        More content here."""
        
        docs = split_project_markdown(test_text)
        if len(docs) > 0:
            print("✓ Text splitter works")
        else:
            print("✗ Text splitter failed")
            return False
            
        # Test embedding (with mock)
        with patch('agentic.utils.embedding.HuggingFaceEmbeddings') as mock_embeddings:
            mock_emb = Mock()
            mock_emb.embed_documents.return_value = [[0.1, 0.2, 0.3]]
            mock_embeddings.return_value = mock_emb
            
            from agentic.utils.embedding import embed_documents
            
            # Create mock documents
            from langchain.schema import Document
            docs = [Document(page_content="Test content")]
            
            embeddings = embed_documents(docs)
            if embeddings:
                print("✓ Embedding function works")
            else:
                print("✗ Embedding function failed")
                return False
                
    except Exception as e:
        print(f"✗ Error testing utilities: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ All utility tests passed!")
    return True

def test_imports():
    """Test that all required modules can be imported"""
    
    print("\n📦 Testing Module Imports")
    print("=" * 30)
    
    try:
        # Test core imports
        import agentic.utils.firebase_client
        print("✓ Firebase client imported")
        
        import agentic.utils.pinecone_client
        print("✓ Pinecone client imported")
        
        import agentic.utils.model_loader
        print("✓ Model loader imported")
        
        import agentic.utils.text_splitter
        print("✓ Text splitter imported")
        
        import agentic.utils.embedding
        print("✓ Embedding utility imported")
        
        # Test tool imports
        import agentic.tool.firebase_tool
        print("✓ Firebase tools imported")
        
        import agentic.tool.scrum_timer
        print("✓ Scrum timer imported")
        
        import agentic.tool.standup_fetcher
        print("✓ Standup fetcher imported")
        
        import agentic.tool.ticket_generator
        print("✓ Ticket generator imported")
        
        import agentic.tool.vector_retriever
        print("✓ Vector retriever imported")
        
        # Test workflow import
        import agent.agenticworkflow
        print("✓ Agentic workflow imported")
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ All imports successful!")
    return True

def main():
    """Run all tests"""
    
    print("🚀 Starting Scrum AI Workflow Tests")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Workflow Components", test_workflow_components),
        ("Tool Functions", test_tools),
        ("Utility Functions", test_utilities)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The workflow is ready to use.")
        print("\nTo run the full workflow:")
        print("1. Set up your environment variables (GROQ_API_KEY, PINECONE_API_KEY, etc.)")
        print("2. Configure Firebase credentials")
        print("3. Run: python main.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()