# R&D Tax Agent - Technical Architecture

## System Overview

An AI agent that analyzes GitHub repositories to identify R&D qualifying activities according to HMRC Corporation Tax R&D Relief guidelines, then generates compliant technical documentation.

## Core Components

### 1. Data Collection Layer
**Purpose**: Extract code, commits, PRs, and documentation from GitHub

**Technologies**:
- `PyGithub` - GitHub API client
- `GitPython` - Git operations (optional, for deep analysis)

**Key Functions**:
```python
def fetch_repo_commits(repo_name: str, since: datetime) -> List[Commit]
def fetch_pull_requests(repo_name: str, since: datetime) -> List[PullRequest]
def fetch_documentation(repo_name: str) -> List[Document]
def analyze_code_changes(commit: Commit) -> CodeAnalysis
```

### 2. HMRC Guidance RAG System
**Purpose**: Retrieve relevant R&D criteria for classification

**Technologies**:
- Azure OpenAI Embeddings (`text-embedding-ada-002`)
- ChromaDB or Azure AI Search
- LangChain (optional, for retrieval chains)

**HMRC R&D Criteria** (from https://www.gov.uk/guidance/corporation-tax-research-and-development-rd-relief):

1. **Advance in Science/Technology**
   - Not just new to the company
   - Overall knowledge/capability in field
   - Appreciable improvement

2. **Scientific/Technological Uncertainty**
   - Not readily deducible by competent professional
   - Requires investigation/analysis

3. **Systematic Investigation/Search**
   - Directly related to resolving uncertainty
   - Systematic approach (not trial and error)

**Key Functions**:
```python
def embed_hmrc_guidance() -> VectorStore
def retrieve_relevant_criteria(code_change: str) -> List[Criterion]
def check_rd_eligibility(activity: Activity, criteria: List[Criterion]) -> bool
```

### 3. Classification Engine
**Purpose**: Analyze code changes against HMRC criteria

**Technologies**:
- Azure OpenAI GPT-4 (via Azure OpenAI Service)
- Structured output (JSON mode or function calling)

**Analysis Dimensions**:
- Technological uncertainty identified?
- Systematic investigation evident?
- Advance achieved (and documented)?
- Evidence quality (commit messages, PR descriptions, tests)

**Key Functions**:
```python
def classify_commit(commit: Commit, hmrc_context: str) -> RDClassification
def analyze_pr_for_rd(pr: PullRequest) -> RDActivity
def score_rd_confidence(activity: RDActivity) -> float  # 0-100%
```

### 4. Narrative Generation
**Purpose**: Generate HMRC-compliant technical descriptions

**Technologies**:
- Azure OpenAI GPT-4 (creative writing mode)
- Templates for each HMRC criterion

**Output Structure**:
```
For each R&D activity:
- Title
- Timeframe
- Technical Challenge (uncertainty)
- Investigation Approach (systematic)
- Outcome (advance achieved)
- Supporting Evidence (commits, PRs, tests)
```

**Key Functions**:
```python
def generate_technical_narrative(activity: RDActivity) -> str
def map_evidence_to_hmrc_criteria(activity: RDActivity) -> EvidenceMap
def format_for_compliance(narrative: str) -> str
```

### 5. Document Assembly
**Purpose**: Generate templated Word/PDF documents

**Technologies**:
- `python-docx` - Word document generation
- `Jinja2` - Template engine
- `docxtpl` - Combine Jinja2 + python-docx

**Template Structure** (HMRC-compliant):
```
1. Executive Summary
2. Company Overview
3. R&D Activities
   3.1 Activity 1
       - Technical Challenge
       - Uncertainty Addressed
       - Systematic Approach
       - Technical Advance
       - Evidence
   3.2 Activity 2
   ...
4. Appendix: Supporting Evidence
```

**Key Functions**:
```python
def populate_template(activities: List[RDActivity]) -> Document
def generate_docx_report(data: ReportData, template_path: str) -> str
def export_to_pdf(docx_path: str) -> str  # optional
```

## Data Models

```python
@dataclass
class Commit:
    sha: str
    message: str
    author: str
    date: datetime
    files_changed: List[str]
    additions: int
    deletions: int
    diff_snippet: str

@dataclass
class PullRequest:
    number: int
    title: str
    description: str
    author: str
    created_at: datetime
    merged_at: Optional[datetime]
    commits: List[Commit]
    labels: List[str]
    comments: List[str]

@dataclass
class RDActivity:
    id: str
    title: str
    description: str
    timeframe: str  # e.g., "Q3 2024"
    
    # HMRC Criteria
    technological_uncertainty: str
    systematic_investigation: str
    technical_advance: str
    
    # Evidence
    commits: List[str]  # SHAs
    pull_requests: List[int]  # PR numbers
    confidence_score: float  # 0-100
    
@dataclass
class RDReport:
    repo_name: str
    analysis_period: tuple[datetime, datetime]
    activities: List[RDActivity]
    generated_at: datetime
```

## Agent Workflow

```
START
  │
  ├─▶ [1] Connect to GitHub repo
  │      └─▶ Fetch commits (last 12 months)
  │      └─▶ Fetch PRs (last 12 months)
  │      └─▶ Fetch README, docs
  │
  ├─▶ [2] For each commit/PR:
  │      └─▶ Extract code changes
  │      └─▶ Retrieve HMRC criteria (RAG)
  │      └─▶ Classify against R&D tests
  │      └─▶ If qualifies → create RDActivity
  │
  ├─▶ [3] Group activities by theme/timeframe
  │
  ├─▶ [4] For each RDActivity:
  │      └─▶ Generate technical narrative
  │      └─▶ Map evidence to HMRC criteria
  │      └─▶ Calculate confidence score
  │
  ├─▶ [5] Assemble report
  │      └─▶ Populate Word template
  │      └─▶ Insert narratives, evidence
  │      └─▶ Format for HMRC compliance
  │
  └─▶ [6] Output .docx file
END
```

## Azure Services Architecture

```
┌──────────────────────────────────────┐
│   GitHub API                         │
│   (External)                         │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│   Azure Function App                 │
│   (Orchestration)                    │
│   - Scheduled trigger (monthly?)     │
│   - Manual trigger via HTTP          │
└──────────┬───────────────────────────┘
           │
           ├────▶ Azure OpenAI Service
           │      (Embeddings + GPT-4)
           │
           ├────▶ Azure AI Search OR ChromaDB
           │      (HMRC guidance vectors)
           │
           ├────▶ Azure Blob Storage
           │      (Generated reports)
           │
           └────▶ Azure Table Storage
                  (Metadata, audit trail)
```

## Security Considerations

1. **GitHub Access**: Use fine-grained Personal Access Tokens (read-only)
2. **Secrets Management**: Azure Key Vault for API keys
3. **Data Retention**: Anonymize/delete after report generation (GDPR)
4. **Audit Trail**: Log all R&D classifications for transparency

## Performance Optimization

1. **Caching**: Cache HMRC embeddings (don't re-embed)
2. **Batching**: Analyze commits in batches (rate limiting)
3. **Async**: Use `asyncio` for parallel API calls
4. **Incremental**: Only analyze new commits since last run

## Next Steps for Implementation

**Phase 1** (Week 1):
- [ ] Set up GitHub API integration
- [ ] Create data models
- [ ] Extract commits from test repo

**Phase 2** (Week 2):
- [ ] Embed HMRC guidance into vector store
- [ ] Build RAG retrieval system
- [ ] Test criteria matching

**Phase 3** (Week 3):
- [ ] Build classification prompts
- [ ] Integrate Azure OpenAI
- [ ] Test on sample commits

**Phase 4** (Week 4):
- [ ] Create Word template
- [ ] Build document generator
- [ ] End-to-end test

## Questions to Resolve

1. **Baseline information**: What is the "baseline" you want to compare against?
   - Previous commits from before certain date?
   - Industry best practices?
   - Company's stated R&D goals?

2. **Template format**: Do you have an existing R&D report template from your tax advisory days?

3. **Human review**: Where in the workflow should human review occur?
   - After classification (review which commits qualify)?
   - After narrative generation (edit the writing)?
   - Final approval only?

4. **Deployment**: Railway again, or Azure Functions?
