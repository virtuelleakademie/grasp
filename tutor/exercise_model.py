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

    @validator('steps')
    def check_sequential_steps(cls, steps):
        for i in range(len(steps) - 1):
            if steps[i].step_number + 1 != steps[i + 1].step_number:
                raise ValueError("Steps should be sequentially numbered.")
        return steps

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
    
    @classmethod
    def create_example(cls) -> "Exercise":
        """
        Create an example Exercise instance for documentation and testing.
        
        Returns:
            An example Exercise instance
        """
        metadata = ExerciseMetadata(
            title="Introduction to ANOVA",
            topic="Statistics",
            level="beginner",
            language="en",
            author="AI Tutor",
            tags=["statistics", "ANOVA", "hypothesis testing"],
            version="1.0"
        )
        
        step1 = Step(
            step_number=1,
            guiding_question="What does ANOVA stand for and what is its primary purpose?",
            guiding_answer="ANOVA stands for Analysis of Variance. Its primary purpose is to determine if there are statistically significant differences between the means of three or more independent groups.",
            image=None
        )
        
        checkpoint = Checkpoint(
            checkpoint_number=1,
            main_question="Given the data in the table, perform a one-way ANOVA test to determine if there are significant differences between the three treatment groups.",
            main_answer="The F-value (10.23) exceeds the critical F-value (3.68) at α=0.05, therefore we reject the null hypothesis and conclude there are significant differences between the treatment groups.",
            image_solution=None,
            steps=[step1]
        )
        
        return cls(
            metadata=metadata,
            first_message="Welcome to this exercise on Analysis of Variance (ANOVA). I'll guide you through understanding and applying this statistical method.",
            end_message="Congratulations! You've completed this exercise on ANOVA. You now understand how to use ANOVA and interpret its results.",
            checkpoints=[checkpoint]
        )
