from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class IterationState(BaseModel):
    """Tracks iteration counts and limits for tutoring progression"""
    total_interactions: int = 0
    step_interactions: int = 0
    checkpoint_interactions: int = 0
    finished: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def increment(self):
        """Increment all interaction counters"""
        self.total_interactions += 1
        self.step_interactions += 1
        self.checkpoint_interactions += 1
        self.last_updated = datetime.utcnow()
    
    def reset_step(self):
        """Reset step interactions when moving to next step"""
        self.step_interactions = 0
        self.last_updated = datetime.utcnow()
    
    def reset_checkpoint(self):
        """Reset checkpoint interactions when moving to next checkpoint"""
        self.checkpoint_interactions = 0
        self.reset_step()
    
    def has_step_iterations_left(self, max_step: int = 2) -> bool:
        """Check if step iterations are within the allowed maximum"""
        return self.step_interactions < max_step
    
    def has_checkpoint_iterations_left(self, max_checkpoint: int = 6) -> bool:
        """Check if checkpoint iterations are within the allowed maximum"""
        return self.checkpoint_interactions < max_checkpoint

class ProgressionState(BaseModel):
    """Tracks current position in exercise progression"""
    current_checkpoint: int = 1
    current_step: int = 1
    exercise_id: str
    session_start: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    def advance_step(self):
        """Move to next step in current checkpoint"""
        self.current_step += 1
        self.last_activity = datetime.utcnow()
    
    def advance_checkpoint(self):
        """Move to next checkpoint and reset step to 1"""
        self.current_checkpoint += 1
        self.current_step = 1
        self.last_activity = datetime.utcnow()
    
    def jump_to_checkpoint(self, checkpoint_num: int):
        """Jump directly to specified checkpoint"""
        self.current_checkpoint = checkpoint_num
        self.current_step = 1
        self.last_activity = datetime.utcnow()