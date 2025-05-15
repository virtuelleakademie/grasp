from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, ClassVar
from datetime import date
import json
from enum import Enum
from pathlib import Path

class DifficultyLevel(str, Enum):
    """Standardized difficulty levels for exercises."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class Step(BaseModel):
    step_number: int = Field(..., ge=1, description="Strictly sequential step number starting from 1")
    guiding_question: str = Field(..., description="A Markdown-formatted question, optionally with LaTeX math")
    guiding_answer: str = Field(..., description="Markdown-formatted answer, optionally with LaTeX")
    image: Optional[str] = Field(None, description="Relative path or URL to an image for this step")

    # Example of a step
    EXAMPLE: ClassVar[Dict] = {
        "step_number": 1,
        "guiding_question": "What is the first derivative of $f(x) = x^2 + 3x$?",
        "guiding_answer": "The first derivative is $f'(x) = 2x + 3$",
        "image": None
    }

    @classmethod
    def create_example(cls) -> "Step":
        """Create an example Step instance."""
        return cls(**cls.EXAMPLE)

class Checkpoint(BaseModel):
    checkpoint_number: int = Field(..., ge=1, description="Sequential checkpoint number starting from 1")
    main_question: str = Field(..., description="The primary problem posed at this checkpoint")
    main_answer: str = Field(..., description="The answer or solution summary for the main question")
    image_solution: Optional[str] = Field(None, description="Optional image illustrating the final solution")
    steps: List[Step] = Field(..., description="Ordered guiding questions and their answers")

class ExerciseMetadata(BaseModel):
    title: str = Field(..., description="Name of the exercise")
    topic: str = Field(..., description="Topic area, e.g., ANOVA, Regression")
    level: Optional[str] = Field(None, description="Intended difficulty level (e.g., beginner, advanced)")
    language: str = Field(..., description="Exercise language (e.g., 'de', 'en')")
    author: Optional[str] = Field(None, description="Author of the exercise")
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords for filtering/search")
    version: Optional[str] = Field("1.0", description="Format or content version")
    date_created: Optional[date] = Field(None, description="Optional creation date")

class Exercise(BaseModel):
    metadata: ExerciseMetadata
    first_message: str = Field(..., description="Tutor's opening message to the student")
    end_message: str = Field(..., description="Final message shown after the last checkpoint")
    checkpoints: List[Checkpoint] = Field(..., description="Sequential learning checkpoints")
