import uuid
from typing import Optional, Tuple
from tutor.models.context import TutorContext
from tutor.models.state import ProgressionState, IterationState  
from tutor.models.responses import Understanding, TutorResponse
from tutor.services.tutor_coordinator import TutorCoordinator
from tutor.exercise_loader import ExerciseLoader

class SessionService:
    """
    High-level session management coordinating all services
    and maintaining session state
    """
    
    def __init__(self):
        self.exercise_loader = ExerciseLoader()
        self.tutor_coordinator = TutorCoordinator()
    
    async def create_session(
        self,
        exercise_name: str,
        tutor_mode: str,
        user_id: str
    ) -> TutorContext:
        """Create a new tutoring session"""
        
        # Load exercise
        exercise_path = f"exercises/{exercise_name}/exercise.yaml"
        exercise = self.exercise_loader.load(exercise_path)
        
        # Create progression state
        progression = ProgressionState(
            current_checkpoint=1,
            current_step=1,
            exercise_id=exercise_name
        )
        
        # Create session context
        context = TutorContext(
            exercise=exercise,
            progression=progression,
            tutor_mode=tutor_mode,
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            iterations=IterationState(),
            current_understanding=Understanding.empty(),
            conversation_history=[]
        )
        
        return context
    
    async def process_message(
        self,
        user_input: str,
        context: TutorContext
    ) -> Tuple[TutorResponse, TutorContext]:
        """Process user input and return updated context"""
        
        # Handle special commands
        if user_input.startswith('/goto'):
            try:
                parts = user_input.split()
                if len(parts) > 1:
                    checkpoint_num = int(parts[1])
                    response = await self.tutor_coordinator.handle_goto_command(checkpoint_num, context)
                    return response, context
                else:
                    response = TutorResponse(
                        feedback_text="Usage: /goto <checkpoint_number>",
                        action="continue_question",
                        next_checkpoint=context.current_checkpoint,
                        next_step=context.current_step
                    )
                    return response, context
            except ValueError:
                response = TutorResponse(
                    feedback_text="Usage: /goto <checkpoint_number> (number must be an integer)",
                    action="continue_question", 
                    next_checkpoint=context.current_checkpoint,
                    next_step=context.current_step
                )
                return response, context
        
        # Process regular message through coordinator
        response = await self.tutor_coordinator.process_student_input(user_input, context)
        
        return response, context
    
    async def get_welcome_message(self, context: TutorContext) -> TutorResponse:
        """Generate initial welcome message for new session"""
        
        welcome_text = f"""
Gruezi! Ich bin heute dein Tutor für Statistik.

{context.exercise.first_message}

Wir werden nun einige Fragen durchgehen, die dir helfen sollen, das Konzept besser zu verstehen. \
Ich werde dir Rückmeldungen und Anleitungen geben, damit du die Aufgaben selbstständig bearbeiten kannst.

Viel Erfolg beim Lernen!

Die Hauptfrage ist:
{context.current_main_question}

Lass uns zuerst über diese Frage nachdenken:
{context.current_guiding_question}
"""
        
        return TutorResponse(
            feedback_text=welcome_text,
            image_path=context.current_image_path,
            action="continue_question",
            next_checkpoint=context.current_checkpoint,
            next_step=context.current_step
        )
    
    def get_session_summary(self, context: TutorContext) -> dict:
        """Get summary of current session state"""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "exercise": context.exercise.metadata.title,
            "tutor_mode": context.tutor_mode,
            "current_checkpoint": context.current_checkpoint,
            "current_step": context.current_step,
            "total_interactions": context.iterations.total_interactions,
            "exercise_complete": context.is_exercise_complete(),
            "conversation_length": len(context.conversation_history)
        }