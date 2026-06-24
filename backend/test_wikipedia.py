#!/usr/bin/env python3
"""
Test script for Wikipedia Service
Run: python test_wikipedia.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.wikipedia_service import wikipedia_service


async def test_search():
    """Test Wikipedia search functionality."""
    print("=" * 60)
    print("TEST 1: Wikipedia Search")
    print("=" * 60)
    
    query = "aspirin"
    print(f"\n🔍 Searching for: '{query}' (English)")
    results = await wikipedia_service.search(query, language="en", limit=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title')}")
        print(f"   Snippet: {result.get('snippet')[:100]}...")


async def test_article_summary():
    """Test getting article summary."""
    print("\n" + "=" * 60)
    print("TEST 2: Get Article Summary")
    print("=" * 60)
    
    article = "Aspirin"
    print(f"\n📖 Fetching summary for: '{article}'")
    summary = await wikipedia_service.get_article_summary(article, language="en", chars=500)
    
    if summary:
        print(f"\n{summary[:500]}...")
    else:
        print("❌ Article not found")


async def test_search_and_summarize():
    """Test search + summarize combo."""
    print("\n" + "=" * 60)
    print("TEST 3: Search + Summarize")
    print("=" * 60)
    
    query = "drug interaction"
    print(f"\n🔎 Searching and summarizing: '{query}'")
    result = await wikipedia_service.search_and_summarize(query, language="en")
    
    if result:
        print(f"\n{result[:600]}...")
    else:
        print("❌ No results found")


async def test_medical_context():
    """Test medical term extraction."""
    print("\n" + "=" * 60)
    print("TEST 4: Medical Context Extraction")
    print("=" * 60)
    
    terms = ["Aspirin", "Ibuprofen", "Hypertension"]
    print(f"\n🏥 Extracting medical info for: {terms}")
    
    results = await wikipedia_service.extract_medical_context(terms, language="en")
    
    for term, summary in results.items():
        if summary:
            print(f"\n✅ {term}:")
            print(f"   {summary[:200]}...")
        else:
            print(f"\n❌ {term}: Not found")


async def test_vietnamese():
    """Test Vietnamese Wikipedia."""
    print("\n" + "=" * 60)
    print("TEST 5: Vietnamese Wikipedia")
    print("=" * 60)
    
    query = "aspirin"
    print(f"\n🇻🇳 Searching in Vietnamese Wikipedia: '{query}'")
    result = await wikipedia_service.search_and_summarize(query, language="vi")
    
    if result:
        print(f"\n{result[:600]}...")
    else:
        print("❌ No results found")


async def main():
    """Run all tests."""
    print("\n" + "🌍 WIKIPEDIA SERVICE TEST SUITE 🌍".center(60))
    
    try:
        await test_search()
        await test_article_summary()
        await test_search_and_summarize()
        await test_medical_context()
        await test_vietnamese()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
