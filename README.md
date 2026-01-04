# R&D Tax Agent

**Automated HMRC R&D Tax Relief Documentation Generator**

Analyzes GitHub repositories to identify R&D qualifying activities and generates HMRC-compliant technical reports.

---

## 🎯 What It Does

This AI agent:

1. **Collects** code, commits, and PRs from your GitHub repository
2. **Analyzes** development activities against [HMRC R&D criteria](https://www.gov.uk/guidance/corporation-tax-research-and-development-rd-relief)
3. **Identifies** qualifying R&D work (technological uncertainty, systematic investigation, technical advance)
4. **Generates** professional Word documents ready for tax advisor review

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- GitHub Personal Access Token ([create one here](https://github.com/settings/tokens))
- Azure OpenAI account ([get access here](https://azure.microsoft.com/en-us/products/ai-services/openai-service))

### Installation

```bash
# Clone or download this project
cd rd-tax-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GITHUB_TOKEN="your_github_token_here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_azure_openai_key"
```

### Run Your First Analysis

```bash
# Quick test (analyze 5 recent commits)
python rd_agent.py facebook/react --test

# Full analysis (last 12 months)
python rd_agent.py your-org/your-repo --company "Your Company Ltd"

# Custom period and confidence threshold
python rd_agent.py your-org/your-repo \
  --months 6 \
  --min-confidence 70 \
  --output my_rd_report.docx \
  --company "Tech Startup Ltd"
```

---

## 📋 Command-Line Options

```
usage: rd_agent.py [-h] [--months MONTHS] [--min-confidence MIN_CONFIDENCE]
                   [--output OUTPUT] [--company COMPANY] [--test]
                   repo

positional arguments:
  repo                  GitHub repository (e.g., facebook/react)

optional arguments:
  --months MONTHS       Number of months to analyze (default: 12)
  --min-confidence MIN_CONFIDENCE
                        Minimum confidence score 0-100 (default: 50)
  --output OUTPUT       Output file path (default: rd_report.docx)
  --company COMPANY     Company name for report
  --test               Quick test mode (5 commits only)
```

---

## 🏗️ Architecture

```
┌──────────────────┐
│  GitHub API      │  Collect commits, PRs, docs
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  HMRC RAG        │  Retrieve relevant R&D criteria
│  (ChromaDB +     │
│   Azure OpenAI)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  R&D Classifier  │  Analyze against HMRC criteria
│  (Azure GPT-4)   │  • Technological uncertainty?
│                  │  • Systematic investigation?
│                  │  • Technical advance?
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Report          │  Generate Word document
│  Generator       │  HMRC-compliant format
└──────────────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `github_collector.py` | Extract code & commits | PyGithub |
| `hmrc_rag.py` | Retrieve R&D criteria | ChromaDB + Azure OpenAI |
| `rd_classifier.py` | Classify activities | Azure GPT-4 |
| `document_generator.py` | Generate reports | python-docx |
| `rd_agent.py` | Main orchestrator | - |

---

## 🔍 How It Works

### HMRC R&D Criteria

The agent evaluates each code change against three core criteria:

#### 1. **Advance in Science/Technology**
- Not just new to your company
- Represents overall knowledge advance in the field
- Appreciable improvement to existing capability

#### 2. **Technological Uncertainty**
- Problem not readily solvable by competent professionals
- Solution not available in existing literature/tools
- Genuine unknowns at project start

#### 3. **Systematic Investigation**
- Structured approach (not trial-and-error)
- Hypothesis testing, experimentation
- Documented evidence of investigation

### Classification Process

For each commit/PR, the agent:

1. **Extracts** technical content (commit messages, code diffs, PR descriptions)
2. **Retrieves** relevant HMRC criteria using semantic search (RAG)
3. **Analyzes** using Azure GPT-4 with structured prompts
4. **Scores** confidence (0-100%) based on evidence quality
5. **Generates** technical narrative if qualifying

### Example Output

A qualifying activity might look like:

```
Title: "Novel Machine Learning Optimizer for Query Performance"

Technological Uncertainty:
"At the project's outset, there was uncertainty whether 
reinforcement learning could adapt to rapidly changing 
query patterns in production databases..."

Systematic Investigation:
"We undertook systematic investigation including: 
(1) Literature review, (2) Design of multiple RL 
architectures, (3) Controlled experimentation..."

Technical Advance:
"Achieved 40% better query throughput than traditional 
optimizers in non-stationary workloads, representing 
new knowledge in database optimization..."

Evidence: PR #145, Commits a1b2c3d, e4f5g6h
Confidence: 85%
```

---

## 📊 Report Structure

Generated Word documents include:

1. **Cover Page** - Company, project, period
2. **Executive Summary** - Overview of R&D activities
3. **Methodology** - How analysis was conducted
4. **R&D Activities** - Detailed narratives for each activity
   - Description
   - Technological Uncertainty
   - Systematic Investigation
   - Technical Advance
   - Supporting Evidence
5. **Appendix** - Full evidence trail (commits, PRs)
6. **Conclusion** - Summary and compliance statement

---

## 🔧 Configuration

### Azure OpenAI Setup

1. Create an Azure OpenAI resource
2. Deploy these models:
   - `text-embedding-ada-002` (for embeddings)
   - `gpt-4` or `gpt-4-32k` (for classification)
3. Get your endpoint and API key

### GitHub Token Setup

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token (classic)
3. Required scopes:
   - `repo` (for private repos)
   - `public_repo` (for public repos only)

### Environment Variables

Create a `.env` file or export:

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-key-here"

# Optional: If your deployments have different names
export AZURE_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
export AZURE_CHAT_DEPLOYMENT="gpt-4"
```

---

## 💡 Use Cases

### 1. Internal R&D Claims
```bash
python rd_agent.py your-company/proprietary-ml-platform \
  --months 12 \
  --company "AI Innovations Ltd" \
  --min-confidence 60
```

### 2. Client Projects (Tax Advisors)
```bash
python rd_agent.py client-org/fintech-app \
  --months 18 \
  --company "Client FinTech Ltd" \
  --min-confidence 70 \
  --output "ClientName_RD_2024.docx"
```

### 3. Retrospective Analysis
```bash
python rd_agent.py archived-project/legacy-system \
  --months 36 \
  --min-confidence 50
```

---

## 🎓 Extending the System

### Add Custom HMRC Criteria

Edit `hmrc_rag.py` to add more guidance chunks:

```python
guidance_chunks = [
    {
        "id": "custom_1",
        "criterion_type": "software",
        "text": "Your custom HMRC interpretation...",
        "section": "Custom Section"
    }
]
```

### Customize Report Templates

Modify `document_generator.py` to adjust:
- Document styling
- Section structure
- Evidence formatting

### Support Other VCS

Create new collector classes for GitLab, Bitbucket, etc.:

```python
class GitLabCollector:
    def fetch_commits(self, project_id, since):
        # Implement GitLab API calls
        pass
```

---

## 🔒 Security & Privacy

### Data Handling

- Code analysis happens via API calls to Azure OpenAI
- No code is stored permanently by the agent
- Generated reports saved locally only
- HMRC guidance cached in local ChromaDB

### Best Practices

1. **Use read-only GitHub tokens** (minimum required scopes)
2. **Store credentials in environment variables** (never commit)
3. **Review generated reports** before submission
4. **Anonymize sensitive code** if needed (redact in final doc)

---

## 🐛 Troubleshooting

### "No qualifying activities found"

- Lower `--min-confidence` threshold (try 40-50)
- Check if commits have meaningful messages
- Verify repo has technical (not just docs) work
- Try `--test` mode to see classification reasoning

### "Rate limit exceeded"

- GitHub: Wait or use a different token
- Azure OpenAI: Increase quota or add delays
- Use `--test` mode for development

### "ChromaDB errors"

- Delete `./chroma_hmrc_db` folder and re-run
- Check write permissions in current directory

### "Azure authentication failed"

- Verify endpoint URL (should include `https://`)
- Check API key is correct
- Confirm deployments are named correctly

---

## 📈 Roadmap

**Planned Features:**

- [ ] Support for GitLab, Bitbucket
- [ ] Integration with Jira, Linear (link tickets to code)
- [ ] Multi-repository analysis (consolidated reports)
- [ ] PDF export option
- [ ] Interactive web UI (Streamlit)
- [ ] Azure Functions deployment (scheduled runs)
- [ ] Enhanced prompts for specific tech stacks (ML, IoT, etc.)

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

This is a proof-of-concept system. Contributions welcome!

Areas for improvement:
- Better HMRC criteria prompts
- Support for more VCS platforms
- Enhanced document templates
- Test coverage
- Performance optimization

---

## 📞 Questions?

**Built by Cat** for automating R&D tax relief documentation.

Based on HMRC guidance: https://www.gov.uk/guidance/corporation-tax-research-and-development-rd-relief

---

## ⚖️ Disclaimer

This tool provides technical analysis to support R&D tax relief claims. It does not:
- Provide tax advice
- Guarantee HMRC acceptance
- Replace professional tax advisors

**Always consult a qualified tax professional** before submitting R&D claims.

---

## 🚦 Getting Started Checklist

- [ ] Install Python 3.9+
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Get GitHub Personal Access Token
- [ ] Set up Azure OpenAI account
- [ ] Deploy embedding and chat models
- [ ] Configure environment variables
- [ ] Run test on public repo (`--test` mode)
- [ ] Analyze your own repo
- [ ] Review generated report
- [ ] Customize for your needs

**You're ready to go! 🎉**
