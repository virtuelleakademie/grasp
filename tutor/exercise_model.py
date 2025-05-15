from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class Step(BaseModel):
    step_number: int = Field(..., ge=1, description="Strictly sequential step number starting from 1")
    guiding_question: str = Field(..., description="A Markdown-formatted question, optionally with LaTeX math")
    guiding_answer: str = Field(..., description="Markdown-formatted answer, optionally with LaTeX")
    image: Optional[str] = Field(None, description="Relative path or URL to an image for this step")

class Checkpoint(BaseModel):
    checkpoint_number: int = Field(..., ge=1, description="Sequential checkpoint number starting from 1")
    main_question: str = Field(..., description="The primary problem posed at this checkpoint")
    main_answer: str = Field(..., description="The answer or solution summary for the main question")
    image_solution: Optional[str] = Field(None, description="Optional image illustrating the final solution")
    steps: List[Step] = Field(..., description="Ordered guiding questions and their answers")

class ExerciseMetadata(BaseModel):
    title: str = Field(..., description="Name of the exercise")
    topic: str = Field(..., description="Topic area, e.g., ANOVA, Regression")
    level: str = Field(..., description="Intended difficulty level (e.g., beginner, advanced)")
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
