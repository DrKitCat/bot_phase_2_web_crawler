"""
R&D Tax Agent - Main Orchestration
Entry point for analyzing GitHub repositories and generating R&D tax relief documentation
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional
import argparse

from github_collector import GitHubCollector, Commit, PullRequest
from hmrc_rag import HMRCGuidanceRAG
from rd_classifier import RDClassifier, RDActivity
from document_generator import RDReportGenerator


class RDTaxAgent:
    """
    Main orchestrator for R&D tax relief automation
    """
    
    def __init__(
        self,
        github_token: str,
        azure_endpoint: str,
        azure_api_key: str,
        company_name: str = ""
    ):
        """
        Initialize R&D Tax Agent
        
        Args:
            github_token: GitHub Personal Access Token
            azure_endpoint: Azure OpenAI endpoint
            azure_api_key: Azure OpenAI API key
            company_name: Your company name for reports
        """
        print("🚀 Initializing R&D Tax Agent...")
        
        # Initialize components
        self.github = GitHubCollector(github_token)
        self.hmrc_rag = HMRCGuidanceRAG(azure_endpoint, azure_api_key)
        self.classifier = RDClassifier(
            azure_endpoint, 
            azure_api_key,
            hmrc_rag=self.hmrc_rag
        )
        self.doc_generator = RDReportGenerator(company_name)
        
        print("✓ All components initialized")
    
    def analyze_repository(
        self,
        repo_name: str,
        months_back: int = 12,
        min_confidence: float = 50.0,
        output_path: str = "rd_report.docx"
    ) -> str:
        """
        Main workflow: Analyze a repository and generate R&D report
        
        Args:
            repo_name: GitHub repository (e.g., "facebook/react")
            months_back: How many months of history to analyze
            min_confidence: Minimum confidence score to include (0-100)
            output_path: Where to save the report
            
        Returns:
            Path to generated report
        """
        print(f"\n📊 Analyzing repository: {repo_name}")
        print(f"   Period: Last {months_back} months")
        print(f"   Minimum confidence: {min_confidence}%\n")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Step 1: Collect data from GitHub
        print("📝 Step 1: Collecting data from GitHub...")
        commits = self.github.fetch_commits(repo_name, since=start_date)
        prs = self.github.fetch_pull_requests(repo_name, since=start_date)
        print(f"   ✓ Found {len(commits)} commits and {len(prs)} PRs")
        
        # Step 2: Ensure HMRC guidance is embedded (only needs to run once)
        print("\n📚 Step 2: Setting up HMRC guidance...")
        if self._should_embed_guidance():
            self.hmrc_rag.embed_hmrc_guidance()
        else:
            print("   ✓ HMRC guidance already embedded")
        
        # Step 3: Classify commits and PRs for R&D eligibility
        print("\n🔍 Step 3: Classifying activities for R&D eligibility...")
        qualifying_activities = []
        
        # Analyze PRs (higher level, better context)
        print(f"   Analyzing {len(prs)} pull requests...")
        for i, pr in enumerate(prs, 1):
            if i % 5 == 0:
                print(f"   Progress: {i}/{len(prs)} PRs analyzed...")
            
            # Get commits for this PR
            pr_commits = [c for c in commits if c.sha in pr.commits]
            
            # Classify PR
            classification = self.classifier.classify_pull_request(pr, pr_commits)
            
            # If qualifies and meets confidence threshold
            if classification.qualifies and classification.confidence_score >= min_confidence:
                # Generate full narrative
                activity = self.classifier.generate_rd_narrative(
                    classification,
                    {
                        'id': f'pr_{pr.number}',
                        'commits': pr.commits,
                        'pull_requests': [pr.number],
                        'created_at': pr.created_at.isoformat()
                    }
                )
                qualifying_activities.append(activity)
                print(f"   ✓ PR #{pr.number} qualifies ({classification.confidence_score:.0f}%): {pr.title[:60]}...")
        
        print(f"\n   Found {len(qualifying_activities)} qualifying R&D activities")
        
        # Step 4: Generate report
        print("\n📄 Step 4: Generating R&D report...")
        report_path = self.doc_generator.generate_report(
            activities=qualifying_activities,
            repo_name=repo_name,
            period_start=start_date,
            period_end=end_date,
            output_path=output_path
        )
        
        # Summary
        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE")
        print("="*60)
        print(f"Repository: {repo_name}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Commits analyzed: {len(commits)}")
        print(f"PRs analyzed: {len(prs)}")
        print(f"Qualifying R&D activities: {len(qualifying_activities)}")
        print(f"Report generated: {report_path}")
        print("="*60)
        
        return report_path
    
    def _should_embed_guidance(self) -> bool:
        """Check if HMRC guidance needs to be embedded"""
        # Simple check - see if collection has data
        try:
            count = self.hmrc_rag.collection.count()
            return count == 0
        except:
            return True
    
    def quick_test(self, repo_name: str, n_commits: int = 5) -> None:
        """
        Quick test on a few commits (for development/testing)
        
        Args:
            repo_name: Repository to test
            n_commits: Number of recent commits to analyze
        """
        print(f"\n🧪 Quick Test Mode: Analyzing {n_commits} recent commits from {repo_name}\n")
        
        # Get recent commits
        commits = self.github.fetch_commits(
            repo_name,
            since=datetime.now() - timedelta(days=30)
        )[:n_commits]
        
        print(f"Analyzing {len(commits)} commits...\n")
        
        for i, commit in enumerate(commits, 1):
            print(f"{'='*60}")
            print(f"Commit {i}/{len(commits)}: {commit.sha[:8]}")
            print(f"Message: {commit.message[:100]}...")
            
            # Classify
            classification = self.classifier.classify_commit(commit)
            
            print(f"\nQualifies: {classification.qualifies}")
            print(f"Confidence: {classification.confidence_score}%")
            print(f"Uncertainty: {classification.has_technological_uncertainty}")
            print(f"Systematic: {classification.has_systematic_investigation}")
            print(f"Advance: {classification.achieves_technical_advance}")
            print(f"\nReasoning: {classification.reasoning[:200]}...")
            print()


def main():
    """Command-line interface"""
    
    parser = argparse.ArgumentParser(
        description='Analyze GitHub repositories for R&D tax relief eligibility'
    )
    
    parser.add_argument(
        'repo',
        help='GitHub repository (e.g., facebook/react)'
    )
    
    parser.add_argument(
        '--months',
        type=int,
        default=12,
        help='Number of months to analyze (default: 12)'
    )
    
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=50.0,
        help='Minimum confidence score (0-100, default: 50)'
    )
    
    parser.add_argument(
        '--output',
        default='rd_report.docx',
        help='Output file path (default: rd_report.docx)'
    )
    
    parser.add_argument(
        '--company',
        default='',
        help='Company name for report'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Quick test mode (analyze 5 recent commits only)'
    )
    
    args = parser.parse_args()
    
    # Get credentials from environment
    github_token = os.getenv('GITHUB_TOKEN')
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    
    if not all([github_token, azure_endpoint, azure_api_key]):
        print("❌ Error: Missing required environment variables:")
        print("   - GITHUB_TOKEN")
        print("   - AZURE_OPENAI_ENDPOINT")
        print("   - AZURE_OPENAI_API_KEY")
        return
    
    # Initialize agent
    agent = RDTaxAgent(
        github_token=github_token,
        azure_endpoint=azure_endpoint,
        azure_api_key=azure_api_key,
        company_name=args.company
    )
    
    # Run analysis
    if args.test:
        agent.quick_test(args.repo)
    else:
        agent.analyze_repository(
            repo_name=args.repo,
            months_back=args.months,
            min_confidence=args.min_confidence,
            output_path=args.output
        )


if __name__ == "__main__":
    main()
