from typing import Dict, Any, Tuple, Optional
from tutor.services.session_service import SessionService
from tutor.models.context import TutorContext
from tutor.models.responses import TutorResponse
from tutor.models.gradio_state import GradioSessionState

class GradioTutorBridge:
    """Handles conversion between Gradio state and PydanticAI context"""
    
    def __init__(self):
        self.session_service = SessionService()
    
    def gradio_to_context(self, gradio_state: GradioSessionState) -> TutorContext:
        """Convert Gradio state to TutorContext"""
        if gradio_state.tutor_context is None:
            raise ValueError("No tutor context available in Gradio state")
        return gradio_state.tutor_context
    
    def context_to_gradio(self, context: TutorContext, gradio_state: GradioSessionState) -> GradioSessionState:
        """Update Gradio state with TutorContext"""
        gradio_state.tutor_context = context
        gradio_state.update_activity()
        return gradio_state
    
    def tutor_response_to_gradio(self, response: TutorResponse, context: TutorContext) -> Dict[str, Any]:
        """Convert TutorResponse to Gradio-compatible format"""
        return {
            'message': response.feedback_text,
            'instructions': response.instruction_text,
            'image_path': response.image_path,
            'solution_image_path': response.solution_image_path,
            'action': response.action,
            'metadata': {
                'next_checkpoint': response.next_checkpoint,
                'next_step': response.next_step,
                'has_progression': response.is_progression(),
                'has_media': response.has_media(),
                'exercise_complete': context.is_exercise_complete()
            }
        }
    
    async def process_chat_message(
        self,
        message: str,
        gradio_state: GradioSessionState
    ) -> Tuple[str, str, GradioSessionState]:
        """Process chat message and return updated state"""
        try:
            if gradio_state.tutor_context is None:
                return "Error: No active session. Please refresh the page.", "", gradio_state
            
            context = self.gradio_to_context(gradio_state)
            
            # Process through service layer
            response, updated_context = await self.session_service.process_message(message, context)
            
            # Update gradio state
            updated_gradio_state = self.context_to_gradio(updated_context, gradio_state)
            
            # Add to chat history
            updated_gradio_state.add_chat_message("user", message)
            
            # Format response
            response_text = response.feedback_text
            if response.instruction_text:
                response_text += f"\n\n{response.instruction_text}"
            
            updated_gradio_state.add_chat_message("assistant", response_text)
            updated_gradio_state.last_response = response
            
            return response_text, "", updated_gradio_state  # Clear input
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            gradio_state.add_chat_message("user", message)
            gradio_state.add_chat_message("assistant", error_msg)
            return error_msg, "", gradio_state
    
    async def initialize_session(
        self,
        exercise_name: str,
        tutor_mode: str,
        user_id: str
    ) -> Tuple[str, GradioSessionState]:
        """Initialize a new tutoring session"""
        try:
            context = await self.session_service.create_session(
                exercise_name=exercise_name,
                tutor_mode=tutor_mode,
                user_id=user_id
            )
            
            # Get welcome message
            welcome_response = await self.session_service.get_welcome_message(context)
            
            # Create Gradio state
            gradio_state = GradioSessionState(user_id=user_id)
            gradio_state.tutor_context = context
            gradio_state.settings['exercise_name'] = exercise_name
            gradio_state.settings['tutor_mode'] = tutor_mode
            
            # Add welcome message to history
            gradio_state.add_chat_message("assistant", welcome_response.feedback_text)
            gradio_state.last_response = welcome_response
            
            return welcome_response.feedback_text, gradio_state
            
        except Exception as e:
            error_msg = f"Error initializing session: {str(e)}"
            gradio_state = GradioSessionState(user_id=user_id)
            gradio_state.add_chat_message("assistant", error_msg)
            return error_msg, gradio_state
    
    def format_chat_history(self, gradio_state: GradioSessionState) -> list:
        """Format chat history for Gradio chatbot component"""
        formatted_history = []
        
        for msg in gradio_state.chat_history:
            if msg["role"] == "user":
                formatted_history.append({"role": "user", "content": msg["content"]})
            else:
                formatted_history.append({"role": "assistant", "content": msg["content"]})
        
        return formatted_history
    
    def get_exercise_info(self, gradio_state: GradioSessionState) -> Dict[str, str]:
        """Get current exercise information for UI display"""
        if gradio_state.tutor_context is None:
            return {
                "title": "No Exercise Loaded",
                "checkpoint": "0",
                "step": "0",
                "progress": "0%",
                "current_question": "Please refresh to load an exercise."
            }
        
        context = gradio_state.tutor_context
        total_checkpoints = len(context.exercise.checkpoints)
        progress_percent = (context.current_checkpoint / total_checkpoints) * 100
        
        return {
            "title": context.exercise.metadata.title,
            "checkpoint": str(context.current_checkpoint),
            "step": str(context.current_step),
            "progress": f"{progress_percent:.0f}%",
            "current_question": context.current_guiding_question
        }