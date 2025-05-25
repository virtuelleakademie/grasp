from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from tutor.models.context import TutorContext
from tutor.models.responses import TutorResponse
import uuid

class GradioSessionState(BaseModel):
    """Comprehensive state model for Gradio interface"""
    
    # Session metadata
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "gradio_user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Tutoring state
    tutor_context: Optional[TutorContext] = None
    chat_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # UI state
    active_tab: str = "tutoring"
    chat_input: str = ""
    
    # Settings
    settings: Dict[str, Any] = Field(default_factory=lambda: {
        'exercise_name': 't-test',
        'tutor_mode': 'socratic',
        'language': 'german',
        'difficulty_level': 3,
        'enable_hints': True,
        'feedback_verbosity': 3
    })
    
    # Evaluation data
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Progress tracking
    progress_data: Dict[str, Any] = Field(default_factory=lambda: {
        'exercises_completed': [],
        'time_spent': {},
        'performance_metrics': {}
    })
    
    # Response cache
    last_response: Optional[TutorResponse] = None
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        return self
    
    def add_chat_message(self, role: str, content: str):
        """Add message to chat history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "checkpoint": self.tutor_context.current_checkpoint if self.tutor_context else 1,
            "step": self.tutor_context.current_step if self.tutor_context else 1
        }
        self.chat_history.append(message)
        self.update_activity()
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history = []
        self.update_activity()
    
    def update_setting(self, key: str, value: Any):
        """Update a setting value"""
        self.settings[key] = value
        self.update_activity()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "exercise": self.settings.get('exercise_name', 'unknown'),
            "tutor_mode": self.settings.get('tutor_mode', 'unknown'),
            "current_checkpoint": self.tutor_context.current_checkpoint if self.tutor_context else 0,
            "current_step": self.tutor_context.current_step if self.tutor_context else 0,
            "total_messages": len(self.chat_history),
            "session_duration_minutes": (self.last_activity - self.created_at).total_seconds() / 60,
            "exercise_complete": self.tutor_context.is_exercise_complete() if self.tutor_context else False
        }
    
    class Config:
        arbitrary_types_allowed = True

def initialize_gradio_state(user_id: str = "gradio_user") -> GradioSessionState:
    """Initialize fresh Gradio session state"""
    return GradioSessionState(user_id=user_id)

def update_state_activity(state: GradioSessionState) -> GradioSessionState:
    """Update last activity timestamp"""
    return state.update_activity()