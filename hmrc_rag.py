"""
HMRC R&D Guidance RAG Module
Embeds and retrieves HMRC Corporation Tax R&D Relief criteria
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from openai import AzureOpenAI
import os


@dataclass
class HMRCCriterion:
    """Represents an HMRC R&D criterion"""
    criterion_type: str  # 'advance', 'uncertainty', 'systematic'
    description: str
    examples: List[str]
    source_section: str
    relevance_score: float = 0.0


class HMRCGuidanceRAG:
    """
    RAG system for HMRC R&D guidance
    Similar to your existing RAG chatbot but specialized for R&D tax criteria
    """
    
    def __init__(
        self,
        azure_endpoint: str,
        azure_api_key: str,
        embedding_deployment: str = "text-embedding-ada-002",
        persist_directory: str = "./chroma_hmrc_db"
    ):
        """
        Initialize HMRC Guidance RAG system
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_key: Azure OpenAI API key
            embedding_deployment: Deployment name for embeddings model
            persist_directory: Where to persist ChromaDB
        """
        # Azure OpenAI client (you're already familiar with this!)
        self.azure_client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version="2024-02-15-preview"
        )
        self.embedding_deployment = embedding_deployment
        
        # ChromaDB for vector storage (just like your existing RAG!)
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="hmrc_rd_guidance",
            metadata={"description": "HMRC R&D Relief Criteria"}
        )
    
    def embed_hmrc_guidance(self) -> None:
        """
        Embed HMRC R&D guidance into vector database
        
        This extracts the key criteria from:
        https://www.gov.uk/guidance/corporation-tax-research-and-development-rd-relief
        
        In production, you'd scrape this page or use official HMRC PDFs
        For now, we'll hardcode the core criteria
        """
        
        # HMRC R&D Criteria (from the official guidance)
        guidance_chunks = [
            {
                "id": "advance_1",
                "criterion_type": "advance",
                "text": """
                Advance in science or technology: An advance in overall knowledge or capability 
                in a field of science or technology (not just your company's own state of knowledge). 
                This includes an appreciable improvement to existing knowledge or capability.
                """,
                "section": "Advance in science or technology"
            },
            {
                "id": "advance_2", 
                "criterion_type": "advance",
                "text": """
                The advance must be in the field of science or technology, not just commercial use 
                of existing technologies. Routine analysis, copying, or adaptation of existing 
                knowledge does not qualify.
                """,
                "section": "Advance in science or technology"
            },
            {
                "id": "uncertainty_1",
                "criterion_type": "uncertainty",
                "text": """
                Scientific or technological uncertainty: The knowledge you're seeking is not 
                readily available or deducible by a competent professional working in the field. 
                The uncertainty must exist at the start of the project.
                """,
                "section": "Scientific or technological uncertainty"
            },
            {
                "id": "uncertainty_2",
                "criterion_type": "uncertainty",
                "text": """
                Examples of technological uncertainty include: whether something is scientifically 
                possible or technologically feasible, how to achieve a scientific or technological 
                advance, which of various technological approaches will work or work better, 
                whether a particular design will be efficient or effective.
                """,
                "section": "Scientific or technological uncertainty"
            },
            {
                "id": "systematic_1",
                "criterion_type": "systematic",
                "text": """
                A systematic investigation or search: Work must be directly related to resolving 
                the scientific or technological uncertainty. It must follow a systematic approach, 
                not just trial and error. This includes hypothesis testing, experimentation, 
                analysis, and iteration.
                """,
                "section": "Systematic investigation"
            },
            {
                "id": "systematic_2",
                "criterion_type": "systematic",
                "text": """
                Qualifying activities include: designing, building, and testing prototypes; 
                developing new or improved materials, products, devices, processes or services; 
                research to resolve technological uncertainties; feasibility studies to inform 
                R&D decisions.
                """,
                "section": "Systematic investigation"
            },
            {
                "id": "evidence_1",
                "criterion_type": "evidence",
                "text": """
                Evidence requirements: You should maintain records of your R&D activities including 
                project plans, test results, design documents, technical reports, and details of 
                the uncertainties you faced and how you resolved them. Failed experiments are 
                important evidence of genuine R&D.
                """,
                "section": "Evidence and documentation"
            },
            {
                "id": "excluded_1",
                "criterion_type": "exclusion",
                "text": """
                Activities that do not qualify: Routine or periodic alterations to existing products, 
                processes, materials, devices, or services, even if improvements result. Work in 
                the arts, humanities or social sciences (unless it supports an R&D project in science 
                or technology). Cosmetic or aesthetic modifications.
                """,
                "section": "Excluded activities"
            },
            {
                "id": "software_1",
                "criterion_type": "software",
                "text": """
                Software development qualifies as R&D when it seeks an advance in the field of 
                software engineering, not just implementing known techniques. Qualifying software 
                R&D includes: developing new algorithms, creating novel architectures, solving 
                complex performance or scalability challenges, advancing AI/ML capabilities.
                """,
                "section": "Software development R&D"
            },
            {
                "id": "software_2",
                "criterion_type": "software",
                "text": """
                Software activities that typically do not qualify: Using established development 
                methods, implementing standard business logic, routine debugging, website design 
                using standard tools, integrating existing software packages without significant 
                customization requiring new technological solutions.
                """,
                "section": "Software development exclusions"
            }
        ]
        
        # Embed each chunk
        print("Embedding HMRC guidance into vector database...")
        
        for chunk in guidance_chunks:
            # Get embedding from Azure OpenAI
            embedding = self._get_embedding(chunk["text"])
            
            # Add to ChromaDB
            self.collection.add(
                ids=[chunk["id"]],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[{
                    "criterion_type": chunk["criterion_type"],
                    "section": chunk["section"]
                }]
            )
        
        print(f"✓ Embedded {len(guidance_chunks)} HMRC guidance chunks")
    
    def retrieve_relevant_criteria(
        self,
        query: str,
        n_results: int = 3
    ) -> List[HMRCCriterion]:
        """
        Retrieve HMRC criteria relevant to a code change or activity
        
        Args:
            query: Description of the code change or technical work
            n_results: Number of relevant criteria to return
            
        Returns:
            List of relevant HMRC criteria
        """
        # Get query embedding
        query_embedding = self._get_embedding(query)
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Convert to HMRCCriterion objects
        criteria = []
        for i in range(len(results['ids'][0])):
            criterion = HMRCCriterion(
                criterion_type=results['metadatas'][0][i]['criterion_type'],
                description=results['documents'][0][i],
                examples=[],  # Could be extracted from text
                source_section=results['metadatas'][0][i]['section'],
                relevance_score=results['distances'][0][i] if 'distances' in results else 0.0
            )
            criteria.append(criterion)
        
        return criteria
    
    def get_criteria_by_type(self, criterion_type: str) -> List[str]:
        """
        Get all criteria of a specific type
        
        Args:
            criterion_type: 'advance', 'uncertainty', 'systematic', etc.
            
        Returns:
            List of criterion descriptions
        """
        results = self.collection.get(
            where={"criterion_type": criterion_type}
        )
        return results['documents']
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector from Azure OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.azure_client.embeddings.create(
            model=self.embedding_deployment,
            input=text
        )
        return response.data[0].embedding


# Example usage
if __name__ == "__main__":
    # Your Azure OpenAI credentials (same as your existing RAG chatbot!)
    AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        print("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        exit(1)
    
    # Initialize RAG system
    rag = HMRCGuidanceRAG(
        azure_endpoint=AZURE_ENDPOINT,
        azure_api_key=AZURE_API_KEY
    )
    
    # Embed HMRC guidance (do this once)
    # rag.embed_hmrc_guidance()
    
    # Test retrieval
    query = """
    Implemented a new machine learning algorithm to optimize database query 
    performance. The existing techniques couldn't handle our data volume, so 
    we had to develop a novel approach combining reinforcement learning with 
    adaptive indexing. Tested multiple hypotheses before finding a solution.
    """
    
    print(f"\nQuery: {query[:100]}...")
    print("\nRelevant HMRC criteria:")
    
    criteria = rag.retrieve_relevant_criteria(query)
    for i, criterion in enumerate(criteria, 1):
        print(f"\n{i}. {criterion.criterion_type.upper()}")
        print(f"   {criterion.description.strip()[:200]}...")
        print(f"   Source: {criterion.source_section}")
