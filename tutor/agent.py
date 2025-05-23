# import time
import os

import chainlit as cl

# Import exercise_loader for loading exercises from files
from tutor.exercise_loader import ExerciseLoader

# Also keep the direct imports for backward compatibility
try:
    from tutor.exercises import main_question, main_answer, guiding_questions, image, image_solution, guiding_answers, first_message, end_message
except ImportError:
    # Define empty defaults if the module is not found
    main_question = {}
    main_answer = {}
    guiding_questions = {}
    image = {}
    image_solution = {}
    guiding_answers = {}
    first_message = ""
    end_message = ""

from tutor.reasoning import client, Understanding, Feedback, Instructions, TutorCheckUnderstanding, TutorFeedback, TutorInstructions
from tutor.helper import with_agent_state

max_interactions_step = 2 ## maximum number of interactions per guiding question
max_interactions_checkpoint = 6 ## maximum number of interactions before moving on to the next checkpoint


class Message:
    """Class to handle messages in the chat."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.image = None

    @with_agent_state
    async def send(self, state=None, to_sidebar=True) -> None:
        """Send the message."""
        message_dict = {"role": "assistant", "content": self.text}
        state["messages"].append(message_dict.copy())
        state["log"].append(message_dict.copy())
        if self.image:
            await self.send_image(to_sidebar=to_sidebar)
        await cl.Message(content=self.text).send()
        if state["iterations"].finished:
            # Use end_message from exercise if available, otherwise from direct import
            end_msg = state["exercise"].end_message if state.get("exercise") else end_message
            await cl.AskUserMessage(content=end_msg, timeout=10).send()
        return

    @with_agent_state
    async def send_image(self, to_sidebar: bool = True, state=None) -> None:
        """Send an image."""
        it = state["iterations"]

        # Create a more unique name for the image with timestamp to avoid caching issues
        import time
        import os
        unique_id = int(time.time())

        # Check if image exists before trying to use it
        if self.image and os.path.exists(self.image):
            element = cl.Image(
                name=f"Visual-CP{it.current_checkpoint}-S{it.current_step}-{unique_id}",
                path=self.image
            )

            # Only update sidebar if to_sidebar is True
            if to_sidebar:
                # Force clear the sidebar first to ensure old elements are removed
                await cl.ElementSidebar.set_elements([])

                # Then set the new element
                await cl.ElementSidebar.set_elements([element])
                await cl.ElementSidebar.set_title(f"Checkpoint {it.current_checkpoint} Image")

            # Always send the image in the chat
            await cl.Message(content="", elements=[element]).send()
        else:
            # Log an error but don't crash if image doesn't exist
            print(f"Warning: Image not found at path '{self.image}'")
        return


    def content(self) -> list[dict]:
        """Get the full content list of the message."""
        content = {}
        if self.image and False: ## code does not work yet
            # Upload the image to the OpenAI API to reference it in the message:
            ### DOES NOT WORK: "image_file" or "file" is not a valid type for the OpenAI API parseq required for structured output
            up = client.files.create(file=open(self.image, "rb"), purpose="vision")
            content.update({"type": "image_file", "image_file": {"file_id": up.id}})
        content.update({"type": "text", "text": self.text})

        return content

    def __add__(self, other) -> 'Message':
        """Concatenate messages."""
        if isinstance(other, Message):
            self.text += other.text
            if other.image:
                self.image = other.image
        elif isinstance(other, str):
            self.text += other
        return self

    def __iadd__(self, other) -> "Message":
        """Concatenate messages."""
        return self.__add__(other)



class Iterations:
    def __init__(self, exercise=None) -> None:
        self.total = 0
        self.step = 0
        self.checkpoint = 0
        self.max_step = max_interactions_step  ## Maximum number of interactions per guiding question
        self.max_checkpoint = max_interactions_checkpoint ## Maximum number of interactions before moving on to the next checkpoint
        self.current_step = 0
        self.current_checkpoint = 0
        self.exercise = exercise

        # Handle the case when using ExerciseLoader
        if exercise:
            self.n_checkpoints = len(exercise.checkpoints)  # Number of checkpoints
            self.n_steps = {i+1: len(checkpoint.steps) for i, checkpoint in enumerate(exercise.checkpoints)}  # Number of steps per checkpoint
        else:
            # Legacy mode: use direct imports
            self.n_checkpoints = len(main_question)  # Number of checkpoints
            self.n_steps = {k: len(v) for k, v in guiding_questions.items()}  # Number of steps in the first checkpoint

        self.finished = False ## set to true, when exercise is finished. triggers closing of chainlit

    def increment(self) -> None:
        self.total += 1
        self.step += 1
        self.checkpoint += 1
        return

    def has_step_iterations_left(self) -> bool:
        """Check if step iterations are within the allowed maximum."""
        return self.step < self.max_step

    def has_checkpoint_iterations_left(self) -> bool:
        """Check if checkpoint iterations are within the allowed maximum."""
        return self.checkpoint < self.max_checkpoint

    def has_another_step(self) -> bool:
        """Check if another guiding question step exists in the current checkpoint."""
        return self.current_step <= self.n_steps[self.current_checkpoint] and not self.finished

    def has_another_checkpoint(self) -> bool:
        """Check if another checkpoint exists."""
        return self.current_checkpoint <= self.n_checkpoints and not self.finished

    def main_question(self) -> str:
        """Get the main question for the current checkpoint."""
        try:
            if self.exercise:
                return self.exercise.checkpoints[self.current_checkpoint-1].main_question
            else:
                return main_question[self.current_checkpoint]
        except IndexError:
            raise IndexError("No more checkpoints available.")

    def main_answer(self) -> str:
        """Get the main answer for the current checkpoint."""
        if self.exercise:
            return self.exercise.checkpoints[self.current_checkpoint-1].main_answer
        else:
            return main_answer[self.current_checkpoint]

    def image(self) -> str:
        """Get the image path for the current checkpoint and step."""
        try:
            if self.exercise:
                img_path = self.exercise.checkpoints[self.current_checkpoint-1].steps[self.current_step-1].image
                return img_path
            else:
                return image[self.current_checkpoint][self.current_step]
        except:
            return None

    def image_solution(self) -> str:
        """Get the image solution path for the current checkpoint."""
        if self.exercise:
            return self.exercise.checkpoints[self.current_checkpoint-1].image_solution
        else:
            return image_solution[self.current_checkpoint]

    def guiding_question(self) -> str:
        """Get the guiding question for the current checkpoint and step."""
        try:
            if self.exercise:
                         def image_solution(self) -> str:
                    """Get the image solution path for the current checkpoint."""
                    try:
                        if self.exercise:
                            solution = self.exercise.checkpoints[self.current_checkpoint-1].image_solution
                            # Return None for null/None values so we can check properly with if
                            return solution if solution else None
                        else:
                            return image_solution.get(self.current_checkpoint)
                    except:
                        return None       return self.exercise.checkpoints[self.current_checkpoint-1].steps[self.current_step-1].guiding_question
            else:
                question = guiding_questions[self.current_checkpoint][self.current_step]
            return question
        except:
            return "All guiding questions have been answered."

    def guiding_answer(self) -> str:
        """Get the guiding answer for the current checkpoint and step."""
        if self.exercise:
            try:
                checkpoint_idx = self.current_checkpoint - 1
                step_idx = self.current_step - 1
                
                # Debug info
                print(f"DEBUG: Getting guiding answer for checkpoint {self.current_checkpoint} (idx: {checkpoint_idx}), step {self.current_step} (idx: {step_idx})")
                
                if checkpoint_idx < 0 or checkpoint_idx >= len(self.exercise.checkpoints):
                    error_msg = f"ERROR: Invalid checkpoint index {checkpoint_idx}. Available checkpoints: {len(self.exercise.checkpoints)}"
                    print(error_msg)
                    return error_msg
                
                checkpoint = self.exercise.checkpoints[checkpoint_idx]
                if step_idx < 0 or step_idx >= len(checkpoint.steps):
                    error_msg = f"ERROR: Invalid step index {step_idx}. Available steps in checkpoint {self.current_checkpoint}: {len(checkpoint.steps)}"
                    print(error_msg)
                    return error_msg
                    
                answer = checkpoint.steps[step_idx].guiding_answer
                if not answer or not answer.strip():
                    error_msg = f"ERROR: Empty guiding_answer for checkpoint {self.current_checkpoint}, step {self.current_step}"
                    print(error_msg)
                    return error_msg
                
                print(f"DEBUG: Successfully retrieved answer: {answer[:50]}...")
                return answer
                
            except Exception as e:
                error_msg = f"ERROR in guiding_answer: {str(e)} (checkpoint: {self.current_checkpoint}, step: {self.current_step})"
                print(error_msg)
                return error_msg
        else:
            # Legacy mode
            try:
                return guiding_answers[self.current_checkpoint][self.current_step]
            except Exception as e:
                error_msg = f"ERROR in legacy guiding_answer: {str(e)}"
                print(error_msg)
                return error_msg

    @with_agent_state
    def load_next_step(self, state=None) -> str:
        """Load the next instruction or advance to the next checkpoint if no iterations are left."""
        # continue with next checkpoint if no iterations are left
        message = Message("")
        if not self.has_checkpoint_iterations_left():
            if state["debugging"]:
                print(f"System: No more iterations left for Checkpoint {self.current_checkpoint}.")
            message += self.load_next_checkpoint()
            return message

        # update counters and state
        self.step = 0
        self.current_step += 1
        state["current_understanding"].guiding_question_answered = False
        state["log"].append_system_message(f"**System:** Move to Checkpoint {self.current_checkpoint}, Step {self.current_step}.")

        # load next question
        if self.has_another_step():
            if state["debugging"]:
                print(f"System: Loading guiding question for Checkpoint {self.current_checkpoint} and Step {self.current_step}.")
            message.image = self.image()
            message += f"\n\nLass uns {'zuerst' if self.current_step == 1 else 'jetzt'} über diese Frage nachdenken:\n"
            message += self.guiding_question()
        else:
            if state["debugging"]:
                print(f"System: Loading main question for Checkpoint {self.current_checkpoint} at Step {self.current_step} > {self.n_steps[self.current_checkpoint]}.")
            message += "Lass uns nun wieder über die eigentliche Frage nachdenken:\n"
            message += self.main_question()
        return message

    @with_agent_state
    def load_next_checkpoint(self, state=None) -> str:
        """Advance to the next checkpoint and load its main question."""
        self.step = 0
        self.checkpoint = 0
        self.current_step = 0
        self.current_checkpoint += 1
        state["current_understanding"].main_question_answered = False
        state["current_understanding"].guiding_question_answered = False
        state["current_understanding"].summary = []
        state["log"].append_system_message(f"**System:** Move on to Checkpoint {self.current_checkpoint}.")

        message = Message("")
        if self.has_another_checkpoint():
            if state["debugging"]:
                print(f"System: Loading main question for Checkpoint {self.current_checkpoint} at Step {self.current_step}.")
            main_question = self.main_question()
            guiding_question = self.load_next_step()
            message += (
                "Die Hauptfrage ist:\n"
                f"{main_question}\n\n"
            )
            message += guiding_question
        else:
            if state["debugging"]:
                print(f"System: No more checkpoints available.")
            self.finished = True
        return message


@with_agent_state
async def starting_message(state=None) -> None:
    """Send a starting message to the user."""
    # Choose first_message from exercise or direct import
    first_msg = state["exercise"].first_message if state.get("exercise") else first_message

    message = Message(f"""
Gruezi! Ich bin heute dein Tutor für Statistik.

{first_msg}

Wir werden nun einige Fragen durchgehen, die dir helfen sollen, das Konzept besser zu verstehen.
Ich werde dir Rückmeldungen und Anleitungen geben, damit du die Aufgaben selbstständig bearbeiten kannst.
Viel Erfolg beim Lernen!
""")
    # This function is a placeholder for the actual inital message.
    message += state["iterations"].load_next_checkpoint()
    await message.send()
    return


@cl.on_message
@with_agent_state
async def chat(input_message: cl.Message, state=None) -> None:
    """Handle incoming messages and respond accordingly."""
    state["log"].write_to_file = True # start writing log to file after first user input
    user_input = input_message.content.strip()
    message_dict = {"role": "user", "content":[{"type": "text", "text": user_input}]}
    state["messages"].append(message_dict.copy())
    state["log"].append(message_dict.copy())

    message = Message("")
    if state["debugging"]:
        message += f"**System:** I'm the chat. I got this message: {user_input}\n\n"

    # update agent state
    iterations = state["iterations"]
    iterations.increment()

    # check students understanding and give feedback
    understanding = await check_understanding(user_input) ### API call
    state["current_understanding"] = understanding

    if state["show_prompts"]:
        message += f"**System**: Check Understanding:\n{understanding.prompt}\n\n"
    if state["show_reasoning"]:
        message += f"**System**: Thought Process:\n{understanding.view_chain_of_thought()}\n\n"
        message += f"**System**: Understanding:\n{understanding.context()}\n\n"

    await message.send() # send message in between agent calls, so agents can see each others output. Well. except for check_understanding, that passes info directly in the code.
    message = Message("")

    ## We generate feedback separately to ensure homogenous check_understanding without specialiced tutor insctructions, which are needed for Feedback.
    feedback = await generate_feedback(user_input)  ### API call
    if state["show_prompts"]:
        message += f"**System**: Generate Feedback:\n{feedback.prompt}\n"
    if state["show_reasoning"]:
        message += f"**System**: Thought Process:\n{feedback.view_chain_of_thought()}\n\n"
    message += f"{feedback.feedback}\n"

    await message.send() # send message in between agent calls, so agents can see each others output. Well. except for check_understanding, that passes info directly in the code.
    message = Message("")

    # generate next instructions based on understanding
    if understanding.main_question_answered or not iterations.has_checkpoint_iterations_left():
        ## moving to the next checkpoint
        if state["debugging"]:
            message += f"\n**System**: Moving to the next checkpoint.\n\n"
        if understanding.main_question_answered:
            message += "\nYou Du hast die **zentrale Frage** richtig beantwortet!\n\n"

        # Display the solution image only if it exists
        if iterations.image_solution():
            message_solution_image = Message("Hier siehst du eine Zusammenfassung der Lösung.")
            message_solution_image.image = iterations.image_solution()
            await message_solution_image.send(to_sidebar=True)

        # Always display the main answer text
        message += "Hier ist die Musterantwort der zentralen Frage: \n"
        message += iterations.main_answer()
        message += "\n\nLass uns mit der nächsten Aufgabe fortfahren.\n"
        await message.send()
        message = Message("")
        message += iterations.load_next_checkpoint()
    elif understanding.guiding_question_answered or not iterations.has_step_iterations_left():
        ## moving to the next guiding question
        if state["debugging"]:
            message += f"**System**: Moving to the next guiding question.\n"
        if understanding.guiding_question_answered:
            message += "\nDu hast die Frage richtig beantwortet!\n\n"
        message += "Hier ist die Musterantwort dieser Frage: \n"
        message += iterations.guiding_answer()
        await message.send()
        message = Message("")
        message += iterations.load_next_step()
    else:
        ## continue with the same guiding question
        if state["debugging"]:
            message += f"**System**: Continuing with the same guiding question.\n"
        message += "\n\n"
        instructions = await generate_instructions(user_input)  ### API call
        if state["show_prompts"]:
            message += f"**System**: Generate Instructions:\n{instructions.prompt}\n"
        if state["show_reasoning"]:
            message += f"**System**: Thought Process:\n{instructions.view_chain_of_thought()}\n\n"
        message += f"{instructions.instructions}"
    await message.send()
    return




## API calls

tutor_instruction = TutorInstructions()
async def generate_instructions(user_input: str) -> str:
    """Generate instructions based on user input."""
    instructions = await tutor_instruction.generate_instructions(user_input)
    return instructions

tutor_feedback = TutorFeedback()
async def generate_feedback(user_input: str) -> Feedback:
    """Generate feedback based on user input."""
    feedback = await tutor_feedback.generate_feedback(user_input)
    return feedback

tutor_check = TutorCheckUnderstanding()
async def check_understanding(user_input: str) -> Understanding:
    """Check if the user understands the concept."""
    understanding = await tutor_check.check_understanding(user_input)
    return understanding
