from typing import Optional
from tutor.agents import understanding_agent, feedback_agent, instruction_agent
from tutor.models.context import TutorContext
from tutor.models.responses import TutorResponse, Understanding, Feedback, Instructions
from tutor.services.progression_service import ProgressionService

class TutorCoordinator:
    """Orchestrates the multi-agent tutoring workflow"""
    
    def __init__(self):
        self.understanding_agent = understanding_agent
        self.feedback_agent = feedback_agent
        self.instruction_agent = instruction_agent
        self.progression_service = ProgressionService()
    
    async def process_student_input(
        self,
        message: str,
        context: TutorContext
    ) -> TutorResponse:
        """
        Main coordination method that processes student input through
        the three-agent pipeline and determines next actions
        """
        try:
            # Add user message to conversation history
            context.add_to_conversation("user", message)
            context.iterations.increment()
            
            # Phase 1: Evaluate Understanding
            understanding = await self._evaluate_understanding(message, context)
            context.current_understanding = understanding
            
            # Phase 2: Generate Feedback
            feedback = await self._generate_feedback(message, context)
            
            # Phase 3: Determine Progression
            progression_action = self.progression_service.determine_next_action(
                understanding, context
            )
            
            # Phase 4: Generate Response Based on Action
            response = await self._create_response(
                feedback, understanding, progression_action, message, context
            )
            
            # Add assistant response to conversation history
            context.add_to_conversation("assistant", response.feedback_text)
            
            return response
            
        except Exception as e:
            return self._create_error_response(str(e), context)
    
    async def _evaluate_understanding(
        self, 
        message: str, 
        context: TutorContext
    ) -> Understanding:
        """Evaluate student understanding using PydanticAI agent"""
        try:
            result = await self.understanding_agent.run(message, deps=context)
            understanding = result.data
            
            # Debug information
            print(f"\n=== UNDERSTANDING DEBUG ===")
            print(f"Student message: '{message}'")
            print(f"Current guiding question: '{context.current_guiding_question}'")
            print(f"Guiding question answered: {understanding.guiding_question_answered}")
            print(f"Main question answered: {understanding.main_question_answered}")
            print(f"Confidence score: {understanding.confidence_score}")
            print(f"Step iterations: {context.iterations.step_interactions}/{context.max_step_iterations}")
            print(f"Checkpoint iterations: {context.iterations.checkpoint_interactions}/{context.max_checkpoint_iterations}")
            print("===========================\n")
            
            return understanding
        except Exception as e:
            print(f"Error in understanding evaluation: {e}")
            return Understanding.empty()
    
    async def _generate_feedback(
        self, 
        message: str, 
        context: TutorContext
    ) -> Feedback:
        """Generate constructive feedback using PydanticAI agent"""
        try:
            result = await self.feedback_agent.run(message, deps=context)
            return result.data
        except Exception as e:
            print(f"Error in feedback generation: {e}")
            return Feedback.empty()
    
    async def _create_response(
        self,
        feedback: Feedback,
        understanding: Understanding,
        action: str,
        message: str,
        context: TutorContext
    ) -> TutorResponse:
        """Create the final response based on determined action"""
        
        if action == "continue_question":
            # Generate instructions for continuing with current question
            instructions = await self._generate_instructions(message, context)
            
            return TutorResponse(
                feedback_text=feedback.feedback,
                instruction_text=instructions.instructions,
                action=action,
                next_checkpoint=context.current_checkpoint,
                next_step=context.current_step,
                image_path=context.current_image_path
            )
        
        elif action == "advance_step":
            # Move to next step
            solution_text = self.progression_service.format_solution_message(understanding, context)
            next_step_content = self.progression_service.get_next_step_content(context)
            
            # Update context for next step
            context.advance_step()
            
            step_message = self.progression_service.format_step_transition_message(context, next_step_content)
            
            return TutorResponse(
                feedback_text=feedback.feedback + "\n\n" + solution_text + step_message,
                solution_text=context.current_guiding_answer,
                next_question=next_step_content.get("question"),
                image_path=next_step_content.get("image_path"),
                action=action,
                next_checkpoint=context.current_checkpoint,
                next_step=context.current_step
            )
        
        elif action == "advance_checkpoint":
            # Move to next checkpoint
            solution_text = self.progression_service.format_solution_message(understanding, context)
            
            # Show solution image if available
            solution_image_path = context.current_solution_image_path
            
            next_checkpoint_content = self.progression_service.get_next_checkpoint_content(context)
            
            if next_checkpoint_content:
                # Update context for next checkpoint
                context.advance_checkpoint()
                
                checkpoint_message = self.progression_service.format_checkpoint_transition_message(
                    context, next_checkpoint_content
                )
                
                full_message = (
                    feedback.feedback + "\n\n" + solution_text + 
                    "\n\nLass uns mit der nächsten Aufgabe fortfahren.\n" + 
                    checkpoint_message
                )
                
                return TutorResponse(
                    feedback_text=full_message,
                    solution_text=context.current_main_answer,
                    solution_image_path=solution_image_path,
                    next_question=next_checkpoint_content.get("first_guiding_question"),
                    image_path=next_checkpoint_content.get("first_image_path"),
                    action=action,
                    next_checkpoint=context.current_checkpoint,
                    next_step=context.current_step
                )
            else:
                # Exercise complete
                context.iterations.finished = True
                return TutorResponse(
                    feedback_text=feedback.feedback + "\n\n" + solution_text,
                    action="finish",
                    completion_message=context.exercise.end_message,
                    next_checkpoint=context.current_checkpoint,
                    next_step=context.current_step
                )
        
        else:  # finish
            context.iterations.finished = True
            return TutorResponse(
                feedback_text=feedback.feedback,
                action="finish",
                completion_message=context.exercise.end_message,
                next_checkpoint=context.current_checkpoint,
                next_step=context.current_step
            )
    
    async def _generate_instructions(
        self, 
        message: str, 
        context: TutorContext
    ) -> Instructions:
        """Generate instructions using PydanticAI agent"""
        try:
            result = await self.instruction_agent.run(message, deps=context)
            return result.data
        except Exception as e:
            print(f"Error in instruction generation: {e}")
            return Instructions.empty()
    
    def _create_error_response(self, error_message: str, context: TutorContext) -> TutorResponse:
        """Create error response when something goes wrong"""
        return TutorResponse(
            feedback_text=f"I encountered an error: {error_message}. Please try again.",
            error_message=error_message,
            action="continue_question",
            next_checkpoint=context.current_checkpoint,
            next_step=context.current_step
        )
    
    async def handle_goto_command(self, checkpoint_num: int, context: TutorContext) -> TutorResponse:
        """Handle jumping to a specific checkpoint"""
        try:
            max_checkpoints = len(context.exercise.checkpoints)
            
            if checkpoint_num < 1 or checkpoint_num > max_checkpoints:
                return TutorResponse(
                    feedback_text=f"Error: Checkpoint {checkpoint_num} does not exist. Available: 1-{max_checkpoints}",
                    action="continue_question",
                    next_checkpoint=context.current_checkpoint,
                    next_step=context.current_step
                )
            
            # Jump to checkpoint
            context.jump_to_checkpoint(checkpoint_num)
            
            # Get content for the new checkpoint
            checkpoint = context.exercise.checkpoints[checkpoint_num - 1]
            first_step = checkpoint.steps[0] if checkpoint.steps else None
            
            message_text = f"Jumped to Checkpoint {checkpoint_num}\n\n"
            message_text += f"Die Hauptfrage ist:\n{checkpoint.main_question}\n\n"
            
            if first_step:
                message_text += f"\n\nLass uns zuerst über diese Frage nachdenken:\n{first_step.guiding_question}"
                image_path = first_step.image
            else:
                message_text += "Lass uns nun wieder über die eigentliche Frage nachdenken:\n"
                message_text += checkpoint.main_question
                image_path = None
            
            return TutorResponse(
                feedback_text=message_text,
                action="continue_question",
                next_checkpoint=context.current_checkpoint,
                next_step=context.current_step,
                image_path=image_path
            )
            
        except Exception as e:
            return self._create_error_response(f"Error jumping to checkpoint: {str(e)}", context)