from typing import Optional
from tutor.models.context import TutorContext
from tutor.models.responses import Understanding, TutorResponse

class ProgressionService:
    """Handles progression logic through exercises"""
    
    def determine_next_action(
        self, 
        understanding: Understanding, 
        context: TutorContext
    ) -> str:
        """
        Determine the next action based on understanding and iteration limits
        
        Returns:
            - "continue_question": Stay on current question
            - "advance_step": Move to next guiding question
            - "advance_checkpoint": Move to next checkpoint
            - "finish": Complete the exercise
        """
        iterations = context.iterations
        
        # Debug information
        print(f"\n=== PROGRESSION DEBUG ===")
        print(f"Main question answered: {understanding.main_question_answered}")
        print(f"Guiding question answered: {understanding.guiding_question_answered}")
        print(f"Step iterations: {iterations.step_interactions}/{context.max_step_iterations}")
        print(f"Checkpoint iterations: {iterations.checkpoint_interactions}/{context.max_checkpoint_iterations}")
        print(f"Has step iterations left: {iterations.has_step_iterations_left(context.max_step_iterations)}")
        print(f"Has checkpoint iterations left: {iterations.has_checkpoint_iterations_left(context.max_checkpoint_iterations)}")
        print(f"Has next step: {self._has_next_step(context)}")
        print(f"Has next checkpoint: {self._has_next_checkpoint(context)}")
        
        # Check if main question is answered or checkpoint limit reached
        if (understanding.main_question_answered or 
            not iterations.has_checkpoint_iterations_left(context.max_checkpoint_iterations)):
            
            if self._has_next_checkpoint(context):
                action = "advance_checkpoint"
                print(f"Action: {action} (main question answered or checkpoint limit reached)")
                print("==========================\n")
                return action
            else:
                action = "finish"
                print(f"Action: {action} (no more checkpoints)")
                print("==========================\n")
                return action
        
        # Check if guiding question is answered or step limit reached
        elif (understanding.guiding_question_answered or 
              not iterations.has_step_iterations_left(context.max_step_iterations)):
            
            if self._has_next_step(context):
                action = "advance_step"
                print(f"Action: {action} (guiding question answered or step limit reached)")
                print("==========================\n")
                return action
            else:
                # No more steps, continue with main question
                action = "continue_question"
                print(f"Action: {action} (no more steps, continue with main question)")
                print("==========================\n")
                return action
        
        else:
            action = "continue_question"
            print(f"Action: {action} (default - continue working on current question)")
            print("==========================\n")
            return action
    
    def get_next_step_content(self, context: TutorContext) -> dict:
        """Get content for the next step"""
        checkpoint_idx = context.current_checkpoint - 1
        next_step_idx = context.current_step  # current_step will be incremented
        
        if (0 <= checkpoint_idx < len(context.exercise.checkpoints)):
            checkpoint = context.exercise.checkpoints[checkpoint_idx]
            
            if next_step_idx < len(checkpoint.steps):
                step = checkpoint.steps[next_step_idx]
                return {
                    "question": step.guiding_question,
                    "answer": step.guiding_answer,
                    "image_path": step.image,
                    "type": "guiding_question"
                }
            else:
                # Return main question if no more steps
                return {
                    "question": checkpoint.main_question,
                    "answer": checkpoint.main_answer,
                    "image_path": None,
                    "type": "main_question"
                }
        
        return {"question": "No more questions available", "answer": "", "image_path": None, "type": "end"}
    
    def get_next_checkpoint_content(self, context: TutorContext) -> Optional[dict]:
        """Get content for the next checkpoint"""
        next_checkpoint_idx = context.current_checkpoint  # will be incremented
        
        if next_checkpoint_idx < len(context.exercise.checkpoints):
            checkpoint = context.exercise.checkpoints[next_checkpoint_idx]
            first_step = checkpoint.steps[0] if checkpoint.steps else None
            
            return {
                "main_question": checkpoint.main_question,
                "main_answer": checkpoint.main_answer,
                "first_guiding_question": first_step.guiding_question if first_step else None,
                "first_image_path": first_step.image if first_step else None,
                "solution_image_path": checkpoint.image_solution,
                "checkpoint_number": next_checkpoint_idx + 1
            }
        
        return None
    
    def _has_next_step(self, context: TutorContext) -> bool:
        """Check if there's another step in current checkpoint"""
        checkpoint_idx = context.current_checkpoint - 1
        if 0 <= checkpoint_idx < len(context.exercise.checkpoints):
            checkpoint = context.exercise.checkpoints[checkpoint_idx]
            return context.current_step < len(checkpoint.steps)
        return False
    
    def _has_next_checkpoint(self, context: TutorContext) -> bool:
        """Check if there's another checkpoint"""
        return context.current_checkpoint < len(context.exercise.checkpoints)
    
    def format_step_transition_message(self, context: TutorContext, step_content: dict) -> str:
        """Format message for step transition"""
        if step_content["type"] == "guiding_question":
            transition_word = "zuerst" if context.current_step == 1 else "jetzt"
            return f"\n\nLass uns {transition_word} über diese Frage nachdenken:\n{step_content['question']}"
        else:
            return f"Lass uns nun wieder über die eigentliche Frage nachdenken:\n{step_content['question']}"
    
    def format_checkpoint_transition_message(self, context: TutorContext, checkpoint_content: dict) -> str:
        """Format message for checkpoint transition"""
        message = f"Die Hauptfrage ist:\n{checkpoint_content['main_question']}\n\n"
        
        if checkpoint_content["first_guiding_question"]:
            message += f"\n\nLass uns zuerst über diese Frage nachdenken:\n{checkpoint_content['first_guiding_question']}"
        else:
            message += "Lass uns nun wieder über die eigentliche Frage nachdenken:\n"
            message += checkpoint_content['main_question']
        
        return message
    
    def format_solution_message(self, understanding: Understanding, context: TutorContext) -> str:
        """Format solution reveal message"""
        message = ""
        
        if understanding.main_question_answered:
            message += "\nDu hast die **zentrale Frage** richtig beantwortet!\n\n"
        elif understanding.guiding_question_answered:
            message += "\nDu hast die Frage richtig beantwortet!\n\n"
        
        # Get appropriate answer
        if understanding.guiding_question_answered and not understanding.main_question_answered:
            message += "Hier ist die Musterantwort dieser Frage: \n"
            message += context.current_guiding_answer
        else:
            message += "Hier ist die Musterantwort der zentralen Frage: \n"
            message += context.current_main_answer
        
        return message