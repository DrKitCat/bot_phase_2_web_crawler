"""
R&D Classification Engine
Uses Azure OpenAI to classify code changes against HMRC R&D criteria
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from openai import AzureOpenAI
import json
from github_collector import Commit, PullRequest
from hmrc_rag import HMRCGuidanceRAG, HMRCCriterion


@dataclass
class RDClassification:
    """Result of classifying a code change for R&D eligibility"""
    qualifies: bool
    confidence_score: float  # 0-100
    
    # HMRC Criteria Assessment
    has_technological_uncertainty: bool
    uncertainty_description: str
    
    has_systematic_investigation: bool
    systematic_approach: str
    
    achieves_technical_advance: bool
    advance_description: str
    
    # Evidence
    evidence_quality: str  # 'strong', 'moderate', 'weak'
    supporting_evidence: List[str]
    
    # Reasoning
    reasoning: str
    limitations: str


@dataclass 
class RDActivity:
    """Represents a qualifying R&D activity for reporting"""
    id: str
    title: str
    description: str
    timeframe: str
    
    # HMRC Criteria (full narratives)
    technological_uncertainty: str
    systematic_investigation: str
    technical_advance: str
    
    # Evidence links
    commits: List[str]  # SHAs
    pull_requests: List[int]
    
    # Metadata
    confidence_score: float
    created_at: str


class RDClassifier:
    """
    Classifies code changes and development activities against HMRC R&D criteria
    """
    
    def __init__(
        self,
        azure_endpoint: str,
        azure_api_key: str,
        chat_deployment: str = "gpt-4",
        hmrc_rag: Optional[HMRCGuidanceRAG] = None
    ):
        """
        Initialize R&D classifier
        
        Args:
            azure_endpoint: Azure OpenAI endpoint
            azure_api_key: Azure OpenAI API key
            chat_deployment: GPT-4 deployment name
            hmrc_rag: Optional HMRC RAG system for context
        """
        self.azure_client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version="2024-02-15-preview"
        )
        self.chat_deployment = chat_deployment
        self.hmrc_rag = hmrc_rag
    
    def classify_commit(
        self,
        commit: Commit,
        hmrc_context: Optional[List[HMRCCriterion]] = None
    ) -> RDClassification:
        """
        Classify a single commit for R&D eligibility
        
        Args:
            commit: Commit object to analyze
            hmrc_context: Optional HMRC criteria context
            
        Returns:
            RDClassification result
        """
        # Get relevant HMRC criteria if RAG is available
        if self.hmrc_rag and not hmrc_context:
            query = f"{commit.message}\n{commit.diff_snippet}"
            hmrc_context = self.hmrc_rag.retrieve_relevant_criteria(query)
        
        # Build prompt
        prompt = self._build_classification_prompt(commit, hmrc_context)
        
        # Call Azure OpenAI with structured output
        response = self.azure_client.chat.completions.create(
            model=self.chat_deployment,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in HMRC R&D tax relief criteria. 
                    Analyze code changes to determine if they qualify as R&D work.
                    Be rigorous but fair in your assessment."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower temperature for consistent classification
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        return RDClassification(
            qualifies=result.get('qualifies', False),
            confidence_score=result.get('confidence_score', 0),
            has_technological_uncertainty=result.get('has_technological_uncertainty', False),
            uncertainty_description=result.get('uncertainty_description', ''),
            has_systematic_investigation=result.get('has_systematic_investigation', False),
            systematic_approach=result.get('systematic_approach', ''),
            achieves_technical_advance=result.get('achieves_technical_advance', False),
            advance_description=result.get('advance_description', ''),
            evidence_quality=result.get('evidence_quality', 'weak'),
            supporting_evidence=result.get('supporting_evidence', []),
            reasoning=result.get('reasoning', ''),
            limitations=result.get('limitations', '')
        )
    
    def classify_pull_request(
        self,
        pr: PullRequest,
        commits: List[Commit]
    ) -> RDClassification:
        """
        Classify an entire pull request (higher-level analysis)
        
        Args:
            pr: PullRequest object
            commits: Associated commits
            
        Returns:
            RDClassification result
        """
        # Get HMRC context based on PR description
        hmrc_context = None
        if self.hmrc_rag:
            query = f"{pr.title}\n{pr.description}"
            hmrc_context = self.hmrc_rag.retrieve_relevant_criteria(query)
        
        # Build prompt for PR-level analysis
        prompt = self._build_pr_classification_prompt(pr, commits, hmrc_context)
        
        response = self.azure_client.chat.completions.create(
            model=self.chat_deployment,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in HMRC R&D tax relief criteria.
                    Analyze pull requests to identify R&D qualifying work."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return RDClassification(
            qualifies=result.get('qualifies', False),
            confidence_score=result.get('confidence_score', 0),
            has_technological_uncertainty=result.get('has_technological_uncertainty', False),
            uncertainty_description=result.get('uncertainty_description', ''),
            has_systematic_investigation=result.get('has_systematic_investigation', False),
            systematic_approach=result.get('systematic_approach', ''),
            achieves_technical_advance=result.get('achieves_technical_advance', False),
            advance_description=result.get('advance_description', ''),
            evidence_quality=result.get('evidence_quality', 'weak'),
            supporting_evidence=result.get('supporting_evidence', []),
            reasoning=result.get('reasoning', ''),
            limitations=result.get('limitations', '')
        )
    
    def generate_rd_narrative(
        self,
        classification: RDClassification,
        commit_or_pr: dict
    ) -> RDActivity:
        """
        Generate a full R&D activity narrative from classification
        
        Args:
            classification: RDClassification result
            commit_or_pr: Dict with activity details
            
        Returns:
            RDActivity with full narratives
        """
        prompt = f"""
        Based on this R&D classification, generate a professional technical narrative 
        suitable for an HMRC R&D tax relief claim.
        
        CLASSIFICATION:
        - Qualifies: {classification.qualifies}
        - Confidence: {classification.confidence_score}%
        - Uncertainty: {classification.uncertainty_description}
        - Systematic Approach: {classification.systematic_approach}
        - Technical Advance: {classification.advance_description}
        
        ACTIVITY DETAILS:
        {json.dumps(commit_or_pr, indent=2)}
        
        Generate a JSON response with:
        {{
            "title": "Brief, clear title for this R&D activity",
            "description": "2-3 paragraph description of the work undertaken",
            "technological_uncertainty": "Detailed explanation of the technological uncertainty that existed at the project's start",
            "systematic_investigation": "Description of the systematic approach taken to resolve the uncertainty",
            "technical_advance": "Explanation of the advance in science/technology achieved",
            "timeframe": "Timeframe of this activity (e.g., 'Q3 2024')"
        }}
        
        Write in professional but clear language. Focus on technical substance, not business benefits.
        """
        
        response = self.azure_client.chat.completions.create(
            model=self.chat_deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical writer specializing in R&D tax documentation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7  # Higher for creative writing
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return RDActivity(
            id=commit_or_pr.get('id', ''),
            title=result['title'],
            description=result['description'],
            timeframe=result['timeframe'],
            technological_uncertainty=result['technological_uncertainty'],
            systematic_investigation=result['systematic_investigation'],
            technical_advance=result['technical_advance'],
            commits=commit_or_pr.get('commits', []),
            pull_requests=commit_or_pr.get('pull_requests', []),
            confidence_score=classification.confidence_score,
            created_at=commit_or_pr.get('created_at', '')
        )
    
    def _build_classification_prompt(
        self,
        commit: Commit,
        hmrc_context: Optional[List[HMRCCriterion]] = None
    ) -> str:
        """Build prompt for commit classification"""
        
        context_section = ""
        if hmrc_context:
            context_section = "\n\nRELEVANT HMRC CRITERIA:\n"
            for criterion in hmrc_context:
                context_section += f"- {criterion.description}\n"
        
        return f"""
        Analyze this commit for R&D tax eligibility according to HMRC criteria.
        
        COMMIT DETAILS:
        SHA: {commit.sha[:8]}
        Author: {commit.author}
        Date: {commit.date}
        Message: {commit.message}
        
        FILES CHANGED: {len(commit.files_changed)} files
        {', '.join(commit.files_changed[:5])}
        
        CODE CHANGES: +{commit.additions}/-{commit.deletions} lines
        
        DIFF SNIPPET:
        {commit.diff_snippet}
        
        {context_section}
        
        HMRC R&D CRITERIA:
        1. ADVANCE: Does this represent an advance in the field of science/technology, not just for this company?
        2. UNCERTAINTY: Was there technological uncertainty that couldn't be readily resolved by a competent professional?
        3. SYSTEMATIC: Was systematic investigation used to resolve the uncertainty?
        
        Respond in JSON format with:
        {{
            "qualifies": boolean,
            "confidence_score": 0-100,
            "has_technological_uncertainty": boolean,
            "uncertainty_description": "What uncertainty existed?",
            "has_systematic_investigation": boolean,
            "systematic_approach": "How was it investigated?",
            "achieves_technical_advance": boolean,
            "advance_description": "What advance was achieved?",
            "evidence_quality": "strong|moderate|weak",
            "supporting_evidence": ["list", "of", "evidence", "points"],
            "reasoning": "Brief explanation of decision",
            "limitations": "Any concerns or weak points in the claim"
        }}
        """
    
    def _build_pr_classification_prompt(
        self,
        pr: PullRequest,
        commits: List[Commit],
        hmrc_context: Optional[List[HMRCCriterion]] = None
    ) -> str:
        """Build prompt for PR classification"""
        
        context_section = ""
        if hmrc_context:
            context_section = "\n\nRELEVANT HMRC CRITERIA:\n"
            for criterion in hmrc_context:
                context_section += f"- {criterion.description}\n"
        
        commits_summary = "\n".join([
            f"- {c.message[:100]}... (+{c.additions}/-{c.deletions})"
            for c in commits[:5]
        ])
        
        return f"""
        Analyze this pull request for R&D tax eligibility according to HMRC criteria.
        
        PR DETAILS:
        Number: #{pr.number}
        Title: {pr.title}
        Author: {pr.author}
        Created: {pr.created_at}
        Status: {'Merged' if pr.merged_at else 'Open'}
        Labels: {', '.join(pr.labels)}
        
        DESCRIPTION:
        {pr.description[:500]}
        
        COMMITS ({len(commits)} total):
        {commits_summary}
        
        COMMENTS ({len(pr.comments)}):
        {pr.comments[0][:200] if pr.comments else 'None'}
        
        {context_section}
        
        Evaluate this PR against HMRC R&D criteria and respond in the same JSON format as commit classification.
        """


# Example usage
if __name__ == "__main__":
    import os
    from datetime import datetime, timedelta
    from github_collector import GitHubCollector
    
    # Initialize components
    AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # Initialize classifier
    classifier = RDClassifier(
        azure_endpoint=AZURE_ENDPOINT,
        azure_api_key=AZURE_API_KEY
    )
    
    # Get some commits to analyze
    github = GitHubCollector(GITHUB_TOKEN)
    commits = github.fetch_commits(
        "facebook/react",
        since=datetime.now() - timedelta(days=30)
    )
    
    # Classify first commit
    if commits:
        print("Analyzing commit:", commits[0].message[:100])
        classification = classifier.classify_commit(commits[0])
        
        print(f"\nQualifies: {classification.qualifies}")
        print(f"Confidence: {classification.confidence_score}%")
        print(f"Reasoning: {classification.reasoning}")
