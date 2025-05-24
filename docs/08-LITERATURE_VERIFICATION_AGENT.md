# Literature Verification Agent Specification

## Overview
The Literature Verification Agent provides fact-checking capabilities by accessing statistical literature and authoritative sources to verify the correctness of student answers beyond the pre-written exercise solutions.

## Purpose & Requirements

### Core Responsibilities
1. **Fact-checking**: Verify student answers against statistical literature
2. **Citation provision**: Provide authoritative sources for corrections
3. **Conceptual validation**: Check if explanations align with statistical theory
4. **Misconception detection**: Identify and flag common statistical misconceptions

### Integration with Existing Agents
- **Works alongside Understanding Agent**: Provides additional verification layer
- **Informs Feedback Agent**: Supplies evidence-based corrections
- **Supports Instruction Agent**: Offers authoritative guidance sources

## Technical Architecture

### Agent Definition
```python
# tutor/agents/literature_verification_agent.py
from pydantic_ai import Agent, RunContext
from tutor.models.responses import LiteratureVerification
from tutor.models.context import TutorContext
from tutor.services.literature_database import LiteratureDatabase

literature_verification_agent = Agent(
    'openai:gpt-4o',
    deps_type=TutorContext,
    output_type=LiteratureVerification,
    system_prompt="""
    You are a statistical literature verification agent with access to authoritative 
    statistical sources. Your role is to fact-check student responses against 
    established statistical theory and provide citations for corrections.
    """
)

@literature_verification_agent.system_prompt
def get_verification_prompt(ctx: RunContext[TutorContext]) -> str:
    current_topic = ctx.deps.get_current_topic()
    return f"""
    Statistical Literature Verification Agent
    
    Current Topic: {current_topic}
    Current Question: {ctx.deps.current_guiding_question}
    
    Your tasks:
    1. Verify the factual accuracy of student responses
    2. Check alignment with established statistical theory
    3. Identify any misconceptions or errors
    4. Provide authoritative citations for corrections
    5. Flag concepts that need additional verification
    
    Available tools:
    - search_literature(query, topic)
    - get_definition(term)
    - check_formula(formula, context)
    - find_examples(concept)
    """

@literature_verification_agent.tool
def search_literature(ctx: RunContext[TutorContext], query: str, topic: str) -> str:
    """Search statistical literature for specific topics"""
    db = LiteratureDatabase()
    results = db.search(
        query=query,
        topic=topic,
        filters={
            'level': 'undergraduate',  # Match student level
            'reliability': 'high',
            'recency': 'last_10_years'
        }
    )
    return db.format_search_results(results)

@literature_verification_agent.tool
def get_authoritative_definition(ctx: RunContext[TutorContext], term: str) -> str:
    """Get authoritative definition of statistical terms"""
    db = LiteratureDatabase()
    definition = db.get_definition(
        term=term,
        sources=['american_statistical_association', 'statistics_textbooks', 'peer_reviewed_journals']
    )
    return definition

@literature_verification_agent.tool
def verify_formula(ctx: RunContext[TutorContext], formula: str, context: str) -> str:
    """Verify mathematical formulas against authoritative sources"""
    db = LiteratureDatabase()
    verification = db.verify_formula(
        formula=formula,
        context=context,
        cross_reference=True
    )
    return verification

@literature_verification_agent.tool
def check_common_misconceptions(ctx: RunContext[TutorContext], concept: str, student_explanation: str) -> str:
    """Check for common statistical misconceptions"""
    db = LiteratureDatabase()
    misconceptions = db.check_misconceptions(
        concept=concept,
        student_text=student_explanation,
        domain='statistics'
    )
    return misconceptions
```

### Response Model
```python
# tutor/models/responses.py (addition)
from pydantic import BaseModel, Field
from typing import List, Optional

class Citation(BaseModel):
    """Individual citation model"""
    source: str
    authors: List[str]
    title: str
    publication: str
    year: int
    doi: Optional[str] = None
    page_numbers: Optional[str] = None
    reliability_score: float = Field(ge=0.0, le=1.0)
    
class LiteratureVerification(BaseModel):
    """Response model for literature verification"""
    is_factually_correct: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Verification results
    verified_claims: List[str] = Field(default_factory=list)
    disputed_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    
    # Misconceptions and errors
    identified_misconceptions: List[str] = Field(default_factory=list)
    conceptual_errors: List[str] = Field(default_factory=list)
    
    # Evidence and citations
    supporting_citations: List[Citation] = Field(default_factory=list)
    contradicting_citations: List[Citation] = Field(default_factory=list)
    additional_reading: List[Citation] = Field(default_factory=list)
    
    # Corrections and clarifications
    suggested_corrections: List[str] = Field(default_factory=list)
    clarifications: List[str] = Field(default_factory=list)
    
    # Metadata
    verification_scope: str = ""  # What aspects were verified
    limitations: List[str] = Field(default_factory=list)  # What couldn't be verified
    
    def has_issues(self) -> bool:
        """Check if verification found any issues"""
        return (len(self.disputed_claims) > 0 or 
                len(self.unsupported_claims) > 0 or 
                len(self.identified_misconceptions) > 0)
    
    def get_correction_summary(self) -> str:
        """Get formatted summary of corrections needed"""
        if not self.has_issues():
            return "No corrections needed."
        
        summary = []
        if self.disputed_claims:
            summary.append(f"Disputed: {'; '.join(self.disputed_claims)}")
        if self.identified_misconceptions:
            summary.append(f"Misconceptions: {'; '.join(self.identified_misconceptions)}")
        if self.suggested_corrections:
            summary.append(f"Corrections: {'; '.join(self.suggested_corrections)}")
        
        return " | ".join(summary)
```

## Literature Database Service

### Database Architecture
```python
# tutor/services/literature_database.py
from typing import List, Dict, Any, Optional
import json
import sqlite3
from pathlib import Path

class LiteratureDatabase:
    """Service for accessing statistical literature and references"""
    
    def __init__(self):
        self.db_path = Path("data/literature.db")
        self.embeddings_service = EmbeddingsService()
        self.init_database()
    
    def init_database(self):
        """Initialize literature database with statistical sources"""
        # Create tables for different types of content
        self._create_tables()
        self._load_statistical_sources()
    
    def _create_tables(self):
        """Create database tables for literature content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    publication TEXT,
                    year INTEGER,
                    doi TEXT,
                    source_type TEXT,  -- textbook, journal, website, standard
                    reliability_score REAL,
                    content_hash TEXT UNIQUE
                );
                
                CREATE TABLE IF NOT EXISTS concepts (
                    id INTEGER PRIMARY KEY,
                    concept_name TEXT NOT NULL,
                    definition TEXT,
                    source_id INTEGER,
                    topic_area TEXT,  -- descriptive, inferential, regression, etc.
                    difficulty_level TEXT,  -- undergraduate, graduate
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                );
                
                CREATE TABLE IF NOT EXISTS formulas (
                    id INTEGER PRIMARY KEY,
                    formula_text TEXT NOT NULL,
                    context TEXT,
                    variables TEXT,  -- JSON of variable definitions
                    source_id INTEGER,
                    concept_id INTEGER,
                    FOREIGN KEY (source_id) REFERENCES sources (id),
                    FOREIGN KEY (concept_id) REFERENCES concepts (id)
                );
                
                CREATE TABLE IF NOT EXISTS misconceptions (
                    id INTEGER PRIMARY KEY,
                    misconception_text TEXT NOT NULL,
                    correct_explanation TEXT,
                    concept_id INTEGER,
                    frequency_score REAL,  -- How common this misconception is
                    FOREIGN KEY (concept_id) REFERENCES concepts (id)
                );
                
                CREATE TABLE IF NOT EXISTS examples (
                    id INTEGER PRIMARY KEY,
                    example_text TEXT NOT NULL,
                    concept_id INTEGER,
                    difficulty_level TEXT,
                    context TEXT,  -- practical, theoretical, etc.
                    FOREIGN KEY (concept_id) REFERENCES concepts (id)
                );
            """)
    
    def _load_statistical_sources(self):
        """Load authoritative statistical sources into database"""
        
        # Load from predefined statistical textbooks and sources
        sources = [
            {
                'title': 'Introduction to Statistical Learning',
                'authors': ['James', 'Witten', 'Hastie', 'Tibshirani'],
                'publication': 'Springer',
                'year': 2021,
                'source_type': 'textbook',
                'reliability_score': 0.95
            },
            {
                'title': 'The Elements of Statistical Learning',
                'authors': ['Hastie', 'Tibshirani', 'Friedman'],
                'publication': 'Springer',
                'year': 2016,
                'source_type': 'textbook',
                'reliability_score': 0.98
            },
            {
                'title': 'Statistical Inference',
                'authors': ['Casella', 'Berger'],
                'publication': 'Cengage Learning',
                'year': 2021,
                'source_type': 'textbook',
                'reliability_score': 0.96
            },
            {
                'title': 'ASA Statistical Guidelines',
                'authors': ['American Statistical Association'],
                'publication': 'ASA',
                'year': 2023,
                'source_type': 'standard',
                'reliability_score': 0.99
            }
        ]
        
        # Load concepts for common statistical topics
        self._load_statistical_concepts()
        
        # Load common misconceptions
        self._load_common_misconceptions()
    
    def search(self, query: str, topic: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """Search literature database for relevant content"""
        filters = filters or {}
        
        # Use embeddings for semantic search
        query_embedding = self.embeddings_service.embed_text(query)
        
        # Search across concepts, formulas, and examples
        results = []
        
        # Search concepts
        concept_results = self._search_concepts(query, topic, filters)
        results.extend(concept_results)
        
        # Search formulas
        formula_results = self._search_formulas(query, topic, filters)
        results.extend(formula_results)
        
        # Search examples
        example_results = self._search_examples(query, topic, filters)
        results.extend(example_results)
        
        # Rank by relevance and reliability
        ranked_results = self._rank_results(results, query_embedding)
        
        return ranked_results[:10]  # Return top 10 results
    
    def get_definition(self, term: str, sources: List[str] = None) -> Dict[str, Any]:
        """Get authoritative definition of statistical term"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Search for term in concepts table
            query = """
                SELECT c.concept_name, c.definition, s.title, s.authors, s.reliability_score
                FROM concepts c
                JOIN sources s ON c.source_id = s.id
                WHERE c.concept_name LIKE ? OR c.definition LIKE ?
                ORDER BY s.reliability_score DESC
            """
            
            cursor.execute(query, (f"%{term}%", f"%{term}%"))
            results = cursor.fetchall()
            
            if results:
                best_match = results[0]
                return {
                    'term': best_match[0],
                    'definition': best_match[1],
                    'source': best_match[2],
                    'authors': best_match[3],
                    'reliability': best_match[4]
                }
            
            return {'error': f'No authoritative definition found for "{term}"'}
    
    def verify_formula(self, formula: str, context: str, cross_reference: bool = True) -> Dict[str, Any]:
        """Verify mathematical formula against authoritative sources"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Search for similar formulas
            query = """
                SELECT f.formula_text, f.context, f.variables, s.title, s.reliability_score
                FROM formulas f
                JOIN sources s ON f.source_id = s.id
                WHERE f.formula_text LIKE ? OR f.context LIKE ?
                ORDER BY s.reliability_score DESC
            """
            
            cursor.execute(query, (f"%{formula}%", f"%{context}%"))
            results = cursor.fetchall()
            
            verification_result = {
                'formula_verified': False,
                'exact_matches': [],
                'similar_formulas': [],
                'context_matches': []
            }
            
            for result in results:
                if self._formulas_match(formula, result[0]):
                    verification_result['formula_verified'] = True
                    verification_result['exact_matches'].append({
                        'formula': result[0],
                        'context': result[1],
                        'source': result[3],
                        'reliability': result[4]
                    })
                else:
                    verification_result['similar_formulas'].append({
                        'formula': result[0],
                        'context': result[1],
                        'source': result[3],
                        'reliability': result[4]
                    })
            
            return verification_result
    
    def check_misconceptions(self, concept: str, student_text: str, domain: str = 'statistics') -> List[Dict]:
        """Check for common statistical misconceptions in student text"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get misconceptions related to the concept
            query = """
                SELECT m.misconception_text, m.correct_explanation, m.frequency_score, c.concept_name
                FROM misconceptions m
                JOIN concepts c ON m.concept_id = c.id
                WHERE c.concept_name LIKE ? OR c.definition LIKE ?
                ORDER BY m.frequency_score DESC
            """
            
            cursor.execute(query, (f"%{concept}%", f"%{concept}%"))
            misconceptions = cursor.fetchall()
            
            detected_misconceptions = []
            
            for misconception in misconceptions:
                # Use text similarity to detect if student text contains misconception
                similarity_score = self._calculate_text_similarity(
                    student_text, 
                    misconception[0]
                )
                
                if similarity_score > 0.7:  # Threshold for misconception detection
                    detected_misconceptions.append({
                        'misconception': misconception[0],
                        'correction': misconception[1],
                        'confidence': similarity_score,
                        'frequency': misconception[2],
                        'concept': misconception[3]
                    })
            
            return detected_misconceptions
    
    def _formulas_match(self, formula1: str, formula2: str) -> bool:
        """Check if two formulas are mathematically equivalent"""
        # Simplified matching - in production, use symbolic math library
        normalized1 = self._normalize_formula(formula1)
        normalized2 = self._normalize_formula(formula2)
        return normalized1 == normalized2
    
    def _normalize_formula(self, formula: str) -> str:
        """Normalize formula for comparison"""
        # Remove whitespace, standardize notation
        import re
        normalized = re.sub(r'\s+', '', formula.lower())
        # Additional normalization rules...
        return normalized
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Use embedding similarity or other NLP techniques
        embedding1 = self.embeddings_service.embed_text(text1)
        embedding2 = self.embeddings_service.embed_text(text2)
        return self.embeddings_service.cosine_similarity(embedding1, embedding2)


class EmbeddingsService:
    """Service for text embeddings and similarity calculations"""
    
    def __init__(self):
        # Initialize embedding model (could use OpenAI, HuggingFace, etc.)
        pass
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # Implementation depends on chosen embedding service
        pass
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        import numpy as np
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
```

## Integration with Existing Agent Workflow

### Enhanced Tutor Coordinator
```python
# tutor/services/tutor_coordinator.py (updated)
from tutor.agents.literature_verification_agent import literature_verification_agent

class TutorCoordinator:
    def __init__(self):
        self.understanding_agent = understanding_agent
        self.feedback_agent = feedback_agent
        self.instruction_agent = instruction_agent
        self.literature_verification_agent = literature_verification_agent
    
    async def process_student_input(
        self,
        message: str,
        context: TutorContext
    ) -> TutorResponse:
        # Phase 1: Evaluate Understanding
        understanding = await self.understanding_agent.run(message, deps=context)
        
        # Phase 2: Literature Verification (if needed)
        literature_verification = None
        if understanding.confidence_score < 0.8 or context.requires_fact_checking():
            literature_verification = await self.literature_verification_agent.run(
                message, deps=context
            )
        
        # Phase 3: Generate Enhanced Feedback
        enhanced_context = context.copy()
        if literature_verification:
            enhanced_context.literature_verification = literature_verification
        
        feedback = await self.feedback_agent.run(message, deps=enhanced_context)
        
        # Phase 4: Determine progression with verification input
        progression_action = self.progression_service.determine_next_action(
            understanding, literature_verification, context
        )
        
        # Phase 5: Create comprehensive response
        response = await self._create_enhanced_response(
            feedback, understanding, literature_verification, 
            progression_action, message, context
        )
        
        return response
    
    async def _create_enhanced_response(
        self,
        feedback: Feedback,
        understanding: Understanding,
        verification: Optional[LiteratureVerification],
        action: str,
        message: str,
        context: TutorContext
    ) -> TutorResponse:
        
        response_text = feedback.feedback
        
        # Add literature-based corrections if needed
        if verification and verification.has_issues():
            response_text += f"\n\n**Fact-checking Note:**\n{verification.get_correction_summary()}"
            
            # Add citations for corrections
            if verification.supporting_citations:
                citations_text = self._format_citations(verification.supporting_citations)
                response_text += f"\n\n**Sources:**\n{citations_text}"
        
        # Continue with normal response creation...
        return TutorResponse(
            feedback_text=response_text,
            literature_verification=verification,
            action=action,
            # ... other fields
        )
    
    def _format_citations(self, citations: List[Citation]) -> str:
        """Format citations for display"""
        formatted = []
        for i, citation in enumerate(citations[:3], 1):  # Limit to 3 citations
            authors_str = ", ".join(citation.authors[:2])  # Limit authors
            if len(citation.authors) > 2:
                authors_str += " et al."
            
            formatted.append(f"{i}. {authors_str} ({citation.year}). {citation.title}. {citation.publication}.")
        
        return "\n".join(formatted)
```

## Data Sources and Content

### Initial Literature Database Content
1. **Statistical Textbooks**
   - Casella & Berger: Statistical Inference
   - James et al.: Introduction to Statistical Learning
   - Hastie et al.: Elements of Statistical Learning
   - Agresti: Categorical Data Analysis

2. **Standards and Guidelines**
   - American Statistical Association guidelines
   - International Statistical Institute recommendations
   - Journal of Statistical Education best practices

3. **Common Statistical Concepts**
   - Hypothesis testing procedures
   - Confidence interval interpretation
   - P-value misconceptions
   - Effect size and practical significance
   - Assumptions for statistical tests

4. **Known Misconceptions Database**
   - P-value = probability hypothesis is true
   - Correlation implies causation
   - Larger sample always better
   - Non-significant = no effect
   - Confidence interval contains true parameter

### Updating and Maintenance
- Regular updates from new statistical literature
- Community contributions and corrections
- Automated quality checks for reliability
- Version control for content changes

This literature verification agent provides a robust fact-checking layer that ensures student answers are evaluated against the broader statistical literature, not just the exercise's predefined answers.