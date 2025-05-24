from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Understanding(BaseModel):
    """Response model for understanding evaluation by PydanticAI agent"""
    main_question_answered: bool = False
    guiding_question_answered: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    identified_concepts: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    summary: List[str] = Field(default_factory=list)
    reasoning: str = ""
    
    @classmethod
    def empty(cls) -> "Understanding":
        """Create empty understanding state"""
        return cls(
            main_question_answered=False,
            guiding_question_answered=False,
            confidence_score=0.5,
            identified_concepts=[],
            misconceptions=[],
            summary=[],
            reasoning=""
        )
    
    def summary_text(self) -> str:
        """Get formatted summary text"""
        if not self.summary:
            return "No previous understanding recorded."
        return "\n".join(f"- {item}" for item in self.summary)

class Feedback(BaseModel):
    """Response model for feedback generation by PydanticAI agent"""
    feedback: str
    positive_aspects: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    encouragement_level: str = Field(default="moderate")  # low, moderate, high
    reasoning: str = ""
    
    @classmethod
    def empty(cls) -> "Feedback":
        """Create empty feedback state"""
        return cls(
            feedback="I'm having trouble processing your response right now. Please try again.",
            positive_aspects=[],
            areas_for_improvement=[],
            encouragement_level="moderate",
            reasoning=""
        )

class Instructions(BaseModel):
    """Response model for instruction generation by PydanticAI agent"""
    instructions: str
    instruction_type: str = "guidance"  # question, hint, explanation, redirect
    follow_up_questions: List[str] = Field(default_factory=list)
    reasoning: str = ""
    
    @classmethod
    def empty(cls) -> "Instructions":
        """Create empty instructions state"""
        return cls(
            instructions="Let me help you think about this step by step. Can you tell me what you understand so far?",
            instruction_type="guidance",
            follow_up_questions=[],
            reasoning=""
        )

class TutorResponse(BaseModel):
    """Comprehensive response from tutor coordinator"""
    feedback_text: str
    instruction_text: Optional[str] = None
    solution_text: Optional[str] = None
    next_question: Optional[str] = None
    
    # Media and Visual Elements
    image_path: Optional[str] = None
    solution_image_path: Optional[str] = None
    
    # Navigation and State
    action: str  # "continue_question", "advance_step", "advance_checkpoint", "finish"
    next_checkpoint: int
    next_step: int
    
    # Additional Information
    completion_message: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def has_media(self) -> bool:
        """Check if response contains media elements"""
        return bool(self.image_path or self.solution_image_path)
    
    def is_progression(self) -> bool:
        """Check if response involves progression to next step/checkpoint"""
        return self.action in ["advance_step", "advance_checkpoint"]