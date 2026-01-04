"""
Demo Script - Quick test of R&D Tax Agent
Tests the classification engine with sample commits
"""

import os
from datetime import datetime
from github_collector import Commit
from rd_classifier import RDClassifier
from openai import AzureOpenAI


def create_sample_commits():
    """Create sample commits for testing"""
    
    # Sample 1: Clearly qualifies (ML research)
    commit1 = Commit(
        sha="abc123def456",
        message="Implement novel attention mechanism for transformer architecture",
        author="Dr. Smith",
        date=datetime(2024, 9, 15),
        files_changed=["models/attention.py", "models/transformer.py", "tests/test_attention.py"],
        additions=450,
        deletions=120,
        diff_snippet="""
        File: models/attention.py
        +class NovelMultiHeadAttention(nn.Module):
        +    def __init__(self, d_model, num_heads, adaptive_scaling=True):
        +        # New approach: adaptive scaling based on input distribution
        +        self.adaptive_scaling = adaptive_scaling
        +        
        +    def forward(self, query, key, value):
        +        # Novel attention computation with dynamic temperature
        +        attention_scores = self.compute_adaptive_attention(query, key)
        """,
        url="https://github.com/example/repo/commit/abc123"
    )
    
    # Sample 2: Borderline (performance optimization)
    commit2 = Commit(
        sha="def456ghi789",
        message="Optimize database query performance using caching",
        author="Jane Doe",
        date=datetime(2024, 9, 20),
        files_changed=["db/query_cache.py", "db/connection_pool.py"],
        additions=200,
        deletions=50,
        diff_snippet="""
        File: db/query_cache.py
        +class QueryCache:
        +    def __init__(self, max_size=1000):
        +        self.cache = LRUCache(max_size)
        +        
        +    def get_or_fetch(self, query):
        +        if query in self.cache:
        +            return self.cache[query]
        +        result = self.execute_query(query)
        +        self.cache[query] = result
        +        return result
        """,
        url="https://github.com/example/repo/commit/def456"
    )
    
    # Sample 3: Does not qualify (routine work)
    commit3 = Commit(
        sha="ghi789jkl012",
        message="Update README and fix typos in documentation",
        author="Bob Wilson",
        date=datetime(2024, 9, 25),
        files_changed=["README.md", "docs/getting-started.md"],
        additions=30,
        deletions=15,
        diff_snippet="""
        File: README.md
        -## Instalation
        +## Installation
        
        -To install this packge, run:
        +To install this package, run:
        """,
        url="https://github.com/example/repo/commit/ghi789"
    )
    
    return [commit1, commit2, commit3]


def test_classifier():
    """Test the R&D classifier on sample commits"""
    
    print("="*70)
    print("R&D TAX AGENT - DEMO TEST")
    print("="*70)
    print()
    
    # Get credentials
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not azure_endpoint or not azure_api_key:
        print("❌ Error: Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        return
    
    # Test Azure connection first
    print("Testing Azure OpenAI connection...")
    try:
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version="2024-02-15-preview"
        )
        response = client.chat.completions.create(
            model="gpt-4",  # Use your deployment name
            messages=[{"role": "user", "content": "Say 'connected' if you can read this"}],
            max_tokens=10
        )
        print(f"✓ Azure OpenAI connected successfully")
        print()
    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        print("\nPlease check:")
        print("  1. Your AZURE_OPENAI_ENDPOINT is correct")
        print("  2. Your AZURE_OPENAI_API_KEY is valid")
        print("  3. You have a 'gpt-4' deployment (or update the model name)")
        return
    
    # Initialize classifier
    print("Initializing R&D classifier...")
    classifier = RDClassifier(
        azure_endpoint=azure_endpoint,
        azure_api_key=azure_api_key,
        chat_deployment="gpt-4"  # Change if your deployment has a different name
    )
    print("✓ Classifier initialized")
    print()
    
    # Get sample commits
    commits = create_sample_commits()
    
    # Test each commit
    for i, commit in enumerate(commits, 1):
        print("="*70)
        print(f"TEST {i}/{len(commits)}")
        print("="*70)
        print(f"Commit: {commit.sha[:8]}")
        print(f"Message: {commit.message}")
        print(f"Files: {len(commit.files_changed)} changed (+{commit.additions}/-{commit.deletions})")
        print()
        
        # Classify
        print("Analyzing with HMRC R&D criteria...")
        try:
            classification = classifier.classify_commit(commit)
            
            print()
            print("RESULTS:")
            print("-"*70)
            print(f"✓ Qualifies for R&D: {classification.qualifies}")
            print(f"✓ Confidence Score: {classification.confidence_score:.1f}%")
            print()
            print("HMRC CRITERIA ASSESSMENT:")
            print(f"  • Technological Uncertainty: {classification.has_technological_uncertainty}")
            if classification.uncertainty_description:
                print(f"    → {classification.uncertainty_description[:100]}...")
            print()
            print(f"  • Systematic Investigation: {classification.has_systematic_investigation}")
            if classification.systematic_approach:
                print(f"    → {classification.systematic_approach[:100]}...")
            print()
            print(f"  • Technical Advance: {classification.achieves_technical_advance}")
            if classification.advance_description:
                print(f"    → {classification.advance_description[:100]}...")
            print()
            print(f"Evidence Quality: {classification.evidence_quality}")
            print()
            print("REASONING:")
            print(f"{classification.reasoning}")
            
            if classification.limitations:
                print()
                print("LIMITATIONS:")
                print(f"{classification.limitations}")
            
        except Exception as e:
            print(f"❌ Error analyzing commit: {e}")
        
        print()
    
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Run: python rd_agent.py facebook/react --test")
    print("  2. Or analyze your own repo: python rd_agent.py your-org/your-repo")
    print()


if __name__ == "__main__":
    test_classifier()
