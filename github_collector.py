"""
GitHub Integration Module
Collects code, commits, PRs, and documentation from GitHub repositories
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from github import Github, Repository, Commit as GHCommit, PullRequest as GHPullRequest
import os


@dataclass
class Commit:
    """Represents a Git commit with R&D-relevant information"""
    sha: str
    message: str
    author: str
    date: datetime
    files_changed: List[str]
    additions: int
    deletions: int
    diff_snippet: str
    url: str


@dataclass
class PullRequest:
    """Represents a GitHub Pull Request"""
    number: int
    title: str
    description: str
    author: str
    created_at: datetime
    merged_at: Optional[datetime]
    commits: List[str]  # commit SHAs
    labels: List[str]
    comments: List[str]
    url: str


@dataclass
class Documentation:
    """Represents repository documentation"""
    filename: str
    content: str
    path: str
    last_updated: datetime


class GitHubCollector:
    """Collects data from GitHub repositories for R&D analysis"""
    
    def __init__(self, github_token: str):
        """
        Initialize GitHub collector
        
        Args:
            github_token: GitHub Personal Access Token
        """
        self.client = Github(github_token)
    
    def fetch_commits(
        self, 
        repo_name: str, 
        since: datetime,
        until: Optional[datetime] = None,
        branch: str = "main"
    ) -> List[Commit]:
        """
        Fetch commits from a repository within a date range
        
        Args:
            repo_name: Repository name (e.g., "owner/repo")
            since: Start date for commit history
            until: End date (defaults to now)
            branch: Branch to analyze
            
        Returns:
            List of Commit objects
        """
        repo = self.client.get_repo(repo_name)
        until = until or datetime.now()
        
        commits = []
        for gh_commit in repo.get_commits(since=since, until=until, sha=branch):
            try:
                # Get commit details
                commit_data = gh_commit.commit
                
                # Extract file changes
                files_changed = [f.filename for f in gh_commit.files] if gh_commit.files else []
                
                # Get diff snippet (first 500 chars for analysis)
                diff_snippet = self._get_diff_snippet(gh_commit)
                
                # Calculate additions/deletions
                additions = gh_commit.stats.additions if gh_commit.stats else 0
                deletions = gh_commit.stats.deletions if gh_commit.stats else 0
                
                commit = Commit(
                    sha=gh_commit.sha,
                    message=commit_data.message,
                    author=commit_data.author.name,
                    date=commit_data.author.date,
                    files_changed=files_changed,
                    additions=additions,
                    deletions=deletions,
                    diff_snippet=diff_snippet,
                    url=gh_commit.html_url
                )
                commits.append(commit)
                
            except Exception as e:
                print(f"Error processing commit {gh_commit.sha}: {e}")
                continue
        
        return commits
    
    def fetch_pull_requests(
        self,
        repo_name: str,
        since: datetime,
        state: str = "all"  # 'open', 'closed', or 'all'
    ) -> List[PullRequest]:
        """
        Fetch pull requests from a repository
        
        Args:
            repo_name: Repository name
            since: Only return PRs created after this date
            state: PR state filter
            
        Returns:
            List of PullRequest objects
        """
        repo = self.client.get_repo(repo_name)
        
        prs = []
        for gh_pr in repo.get_pulls(state=state, sort='created', direction='desc'):
            # Filter by date
            if gh_pr.created_at < since:
                break  # PRs are sorted by creation date, so we can stop here
            
            try:
                # Extract comments
                comments = [comment.body for comment in gh_pr.get_issue_comments()]
                
                # Extract commit SHAs
                commit_shas = [commit.sha for commit in gh_pr.get_commits()]
                
                pr = PullRequest(
                    number=gh_pr.number,
                    title=gh_pr.title,
                    description=gh_pr.body or "",
                    author=gh_pr.user.login,
                    created_at=gh_pr.created_at,
                    merged_at=gh_pr.merged_at,
                    commits=commit_shas,
                    labels=[label.name for label in gh_pr.labels],
                    comments=comments,
                    url=gh_pr.html_url
                )
                prs.append(pr)
                
            except Exception as e:
                print(f"Error processing PR #{gh_pr.number}: {e}")
                continue
        
        return prs
    
    def fetch_documentation(
        self,
        repo_name: str,
        patterns: List[str] = None
    ) -> List[Documentation]:
        """
        Fetch documentation files from repository
        
        Args:
            repo_name: Repository name
            patterns: File patterns to match (e.g., ['README.md', 'docs/*.md'])
            
        Returns:
            List of Documentation objects
        """
        if patterns is None:
            patterns = ['README.md', 'CHANGELOG.md', 'docs/**/*.md']
        
        repo = self.client.get_repo(repo_name)
        docs = []
        
        # Fetch README
        try:
            readme = repo.get_readme()
            docs.append(Documentation(
                filename=readme.name,
                content=readme.decoded_content.decode('utf-8'),
                path=readme.path,
                last_updated=datetime.now()  # GitHub API doesn't provide this easily
            ))
        except:
            pass
        
        # TODO: Implement recursive search for documentation files
        # This would require walking the repository tree
        
        return docs
    
    def _get_diff_snippet(self, commit: GHCommit, max_chars: int = 500) -> str:
        """
        Extract a snippet of the commit diff for LLM analysis
        
        Args:
            commit: GitHub commit object
            max_chars: Maximum characters to include
            
        Returns:
            Diff snippet string
        """
        try:
            diff_parts = []
            for file in commit.files[:3]:  # Limit to first 3 files
                if file.patch:
                    diff_parts.append(f"File: {file.filename}\n{file.patch[:200]}")
            
            diff_text = "\n\n".join(diff_parts)
            return diff_text[:max_chars]
        except:
            return ""


# Example usage
if __name__ == "__main__":
    # Set your GitHub token
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    if not GITHUB_TOKEN:
        print("Please set GITHUB_TOKEN environment variable")
        exit(1)
    
    # Initialize collector
    collector = GitHubCollector(GITHUB_TOKEN)
    
    # Fetch last 3 months of commits
    repo_name = "torvalds/linux"  # Example repo
    since_date = datetime.now() - timedelta(days=90)
    
    print(f"Fetching commits from {repo_name} since {since_date.date()}...")
    commits = collector.fetch_commits(repo_name, since=since_date)
    print(f"Found {len(commits)} commits")
    
    # Show sample commit
    if commits:
        sample = commits[0]
        print(f"\nSample commit:")
        print(f"  SHA: {sample.sha[:8]}")
        print(f"  Author: {sample.author}")
        print(f"  Message: {sample.message[:100]}...")
        print(f"  Files: {len(sample.files_changed)} changed")
        print(f"  Changes: +{sample.additions}/-{sample.deletions}")
