from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from tutor.exercise_model import Exercise
from tutor.models.state import IterationState, ProgressionState
from tutor.models.responses import Understanding

class TutorContext(BaseModel):
    """
    Central context object that contains all state needed by agents
    and services throughout the tutoring session
    """
    
    # Exercise Information
    exercise: Exercise
    progression: ProgressionState
    
    # Session Configuration
    tutor_mode: str = Field(pattern="^(socratic|instructional)$")
    user_id: str
    session_id: str
    
    # State Management
    iterations: IterationState = Field(default_factory=IterationState)
    current_understanding: Understanding = Field(default_factory=Understanding.empty)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Configuration
    max_step_iterations: int = 2
    max_checkpoint_iterations: int = 6
    
    # Computed Properties
    @property
    def current_checkpoint(self) -> int:
        """Get current checkpoint number"""
        return self.progression.current_checkpoint
    
    @property
    def current_step(self) -> int:
        """Get current step number"""
        return self.progression.current_step
    
    @property
    def current_main_question(self) -> str:
        """Get the main question for current checkpoint"""
        checkpoint_idx = self.current_checkpoint - 1
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            return self.exercise.checkpoints[checkpoint_idx].main_question
        return "No more checkpoints available"
    
    @property
    def current_guiding_question(self) -> str:
        """Get the guiding question for current step"""
        checkpoint_idx = self.current_checkpoint - 1
        step_idx = self.current_step - 1
        
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            checkpoint = self.exercise.checkpoints[checkpoint_idx]
            if 0 <= step_idx < len(checkpoint.steps):
                return checkpoint.steps[step_idx].guiding_question
            else:
                # No more steps, return main question
                return checkpoint.main_question
        return "No question available"
    
    @property
    def current_main_answer(self) -> str:
        """Get the main answer for current checkpoint"""
        checkpoint_idx = self.current_checkpoint - 1
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            return self.exercise.checkpoints[checkpoint_idx].main_answer
        return ""
    
    @property
    def current_guiding_answer(self) -> str:
        """Get the guiding answer for current step"""
        checkpoint_idx = self.current_checkpoint - 1
        step_idx = self.current_step - 1
        
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            checkpoint = self.exercise.checkpoints[checkpoint_idx]
            if 0 <= step_idx < len(checkpoint.steps):
                return checkpoint.steps[step_idx].guiding_answer
        return ""
    
    @property
    def current_image_path(self) -> Optional[str]:
        """Get image path for current step"""
        checkpoint_idx = self.current_checkpoint - 1
        step_idx = self.current_step - 1
        
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            checkpoint = self.exercise.checkpoints[checkpoint_idx]
            if 0 <= step_idx < len(checkpoint.steps):
                return checkpoint.steps[step_idx].image
        return None
    
    @property
    def current_solution_image_path(self) -> Optional[str]:
        """Get solution image path for current checkpoint"""
        checkpoint_idx = self.current_checkpoint - 1
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            return self.exercise.checkpoints[checkpoint_idx].image_solution
        return None
    
    def add_to_conversation(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "checkpoint": self.current_checkpoint,
            "step": self.current_step
        })
    
    def advance_step(self):
        """Advance to next step and reset step iterations"""
        self.progression.advance_step()
        self.iterations.reset_step()
    
    def advance_checkpoint(self):
        """Advance to next checkpoint and reset all counters"""
        self.progression.advance_checkpoint()
        self.iterations.reset_checkpoint()
        self.current_understanding = Understanding.empty()
    
    def jump_to_checkpoint(self, checkpoint_num: int):
        """Jump to specific checkpoint"""
        self.progression.jump_to_checkpoint(checkpoint_num)
        self.iterations.reset_checkpoint()
        self.current_understanding = Understanding.empty()
    
    def is_exercise_complete(self) -> bool:
        """Check if the exercise is complete"""
        return (self.current_checkpoint > len(self.exercise.checkpoints) or
                self.iterations.finished)
    
    def has_next_step(self) -> bool:
        """Check if there's another step in current checkpoint"""
        checkpoint_idx = self.current_checkpoint - 1
        if 0 <= checkpoint_idx < len(self.exercise.checkpoints):
            checkpoint = self.exercise.checkpoints[checkpoint_idx]
            return self.current_step <= len(checkpoint.steps)
        return False
    
    def has_next_checkpoint(self) -> bool:
        """Check if there's another checkpoint"""
        return self.current_checkpoint < len(self.exercise.checkpoints)
    
    class Config:
        # Allow additional fields for future extensibility
        extra = "forbid"
        # Validate assignments to catch errors early
        validate_assignment = True