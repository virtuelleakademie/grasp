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
                return self.exercise.checkpoints[self.current_checkpoint-1].steps[self.current_step-1].guiding_question
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
                # Use current_step directly as the step index since steps are 1-indexed in the exercise
                # but we need to access the step we just completed
                step_idx = self.current_step - 1

                if checkpoint_idx < 0 or checkpoint_idx >= len(self.exercise.checkpoints):
                    return ""

                checkpoint = self.exercise.checkpoints[checkpoint_idx]

                # If step_idx is out of range, we might be trying to get the last step's answer
                # after current_step was already incremented
                if step_idx >= len(checkpoint.steps):
                    step_idx = len(checkpoint.steps) - 1

                if step_idx < 0 or step_idx >= len(checkpoint.steps):
                    return ""

                answer = checkpoint.steps[step_idx].guiding_answer
                if not answer or not answer.strip():
                    return ""

                return answer

            except Exception as e:
                return ""
        else:
            # Legacy mode
            try:
                return guiding_answers[self.current_checkpoint][self.current_step]
            except Exception as e:
                return ""

    @with_agent_state
    def load_next_step(self, state=None) -> Message:
        """Load the next instruction or advance to the next checkpoint if no iterations are left."""
        # update counters and state
        self.step = 0
        self.current_step += 1
        state["log"].append_system_message(f"**System:** Move to Checkpoint {self.current_checkpoint}, Step {self.current_step}.")

        # load next question
        message = Message("")
        if self.has_another_step():
            # Only reset guiding_question_answered when moving to a NEW guiding question
            state["current_understanding"].guiding_question_answered = False
            if state["debugging"]:
                print(f"System: Loading guiding question for Checkpoint {self.current_checkpoint} and Step {self.current_step}.")
            message.image = self.image()
            message += f"\n\nLass uns {'zuerst' if self.current_step == 1 else 'jetzt'} über diese Frage nachdenken:\n"
            message += self.guiding_question()
        else:
            # Don't reset guiding_question_answered when moving to main question
            # The previous guiding question was answered correctly
            if state["debugging"]:
                print(f"System: Loading main question for Checkpoint {self.current_checkpoint} at Step {self.current_step} > {self.n_steps[self.current_checkpoint]}.")
            message += "Lass uns nun wieder über die eigentliche Frage nachdenken:\n"
            message += self.main_question()
        return message

    @with_agent_state
    async def clear_sidebar_if_no_image(self, state=None) -> None:
        """Clear the sidebar if the current checkpoint has no solution image and no step image."""
        # Only clear if there's no solution image AND no current step image
        if not self.image_solution() and not self.image():
            await cl.ElementSidebar.set_elements([])
            await cl.ElementSidebar.set_title("")

    @with_agent_state
    def load_next_checkpoint(self, state=None) -> Message:
        """Advance to the next checkpoint and load its main question."""
        self.step = 0
        self.checkpoint = 0
        self.current_step = 1
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
            message += f"Die Hauptfrage ist:\n{main_question}\n\n"

            # Handle first step directly to preserve image
            if self.has_another_step():
                # Set the image for the first step
                message.image = self.image()
                message += f"\n\nLass uns zuerst über diese Frage nachdenken:\n"
                message += self.guiding_question()
            else:
                message += "Lass uns nun wieder über die eigentliche Frage nachdenken:\n"
                message += self.main_question()

            # Update state for the first step
            state["current_understanding"].guiding_question_answered = False
            state["log"].append_system_message(f"**System:** Move to Checkpoint {self.current_checkpoint}, Step {self.current_step}.")
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

Wir werden nun einige Fragen durchgehen, die dir helfen sollen, das Konzept besser zu verstehen. \
Ich werde dir Rückmeldungen und Anleitungen geben, damit du die Aufgaben selbstständig bearbeiten kannst.\n
Viel Erfolg beim Lernen! \n
""")
    # This function is a placeholder for the actual inital message.
    checkpoint_message = state["iterations"].load_next_checkpoint()
    message += checkpoint_message
    message.image = checkpoint_message.image  # Preserve the image
    await message.send()
    # Clear sidebar if the first checkpoint has no solution image and no step image
    await state["iterations"].clear_sidebar_if_no_image()
    return


@cl.on_message
@with_agent_state
async def chat(input_message: cl.Message, state=None) -> None:
    """Handle incoming messages and respond accordingly."""
    state["log"].write_to_file = True # start writing log to file after first user input
    user_input = input_message.content.strip()

    # Special command to jump to a specific checkpoint
    if user_input.startswith("/goto"):
        try:
            # Make sure os is imported for path handling
            import os

            parts = user_input.split()
            if len(parts) > 1:
                checkpoint_num = int(parts[1])
                if checkpoint_num < 1:
                    await Message("Checkpoint number must be at least 1").send()
                    return

                iterations = state["iterations"]
                if checkpoint_num > iterations.n_checkpoints:
                    await Message(f"Error: Maximum checkpoint is {iterations.n_checkpoints}").send()
                    return

                # Send confirmation message
                message = Message(f"Jumping to Checkpoint {checkpoint_num}")
                await message.send()

                # Reset progression variables
                iterations.step = 0
                iterations.checkpoint = 0
                iterations.current_step = 0

                # The current_checkpoint is 0-based internally, but 1-based in display
                iterations.current_checkpoint = checkpoint_num - 1

                # Reset understanding state
                state["current_understanding"].main_question_answered = False
                state["current_understanding"].guiding_question_answered = False
                state["current_understanding"].summary = []

                # Add system log message
                state["log"].append_system_message(f"**System:** Jumped to Checkpoint {checkpoint_num}.")

                # Get the main question
                try:
                    if iterations.exercise:
                        # Check if checkpoint index is valid
                        if 0 <= iterations.current_checkpoint < len(iterations.exercise.checkpoints):
                            main_question = iterations.exercise.checkpoints[iterations.current_checkpoint].main_question
                        else:
                            raise IndexError(f"Checkpoint index {iterations.current_checkpoint} out of range (0-{len(iterations.exercise.checkpoints)-1})")
                    else:
                        from exercises import main_question as main_q_dict
                        main_question = main_q_dict[iterations.current_checkpoint + 1]  # Adjust indexing for legacy mode
                except Exception as e:
                    print(f"Error getting main question: {str(e)}")
                    main_question = "Error loading main question"

                # Load first guiding question
                try:
                    if iterations.exercise:
                        # Check if checkpoint and step indices are valid
                        if 0 <= iterations.current_checkpoint < len(iterations.exercise.checkpoints):
                            checkpoint = iterations.exercise.checkpoints[iterations.current_checkpoint]
                            if len(checkpoint.steps) > 0:
                                guiding_question = checkpoint.steps[0].guiding_question
                                image_path = checkpoint.steps[0].image
                            else:
                                raise IndexError(f"No steps found in checkpoint {iterations.current_checkpoint}")
                        else:
                            raise IndexError(f"Checkpoint index {iterations.current_checkpoint} out of range")
                    else:
                        from exercises import guiding_questions
                        guiding_question = guiding_questions[iterations.current_checkpoint + 1][1]
                        image_path = None
                except Exception as e:
                    print(f"Error getting guiding question: {str(e)}")
                    guiding_question = "Error loading guiding question"
                    image_path = None

                # Create message text
                message_text = f"Die Hauptfrage ist:\n{main_question}\n\n"
                message_text += f"\n\nLass uns zuerst über diese Frage nachdenken:\n{guiding_question}"

                # Send the combined message
                checkpoint_message = Message(message_text)

                # Handle image if it exists
                if image_path:
                    print(f"Loading image: {image_path}")
                    # Construct full path if needed
                    if iterations.exercise:
                        # No need to reconstruct the path - it should already be absolute
                        # from the ExerciseLoader._adjust_paths method
                        full_image_path = image_path
                        print(f"Full image path: {full_image_path}")
                        if os.path.exists(full_image_path):
                            checkpoint_message.image = full_image_path
                        else:
                            print(f"Warning: Image not found at {full_image_path}")
                    else:
                        checkpoint_message.image = image_path

                await checkpoint_message.send()

                # Update current step for future progression
                iterations.current_step = 1

                # For debugging
                if state["debugging"]:
                    print(f"System: Jumped to Checkpoint {checkpoint_num}")
                    print(f"Current step: {iterations.current_step}, Current checkpoint: {iterations.current_checkpoint}")
                    print(f"Main question: {main_question[:50]}...")

                # Clear sidebar if needed
                await iterations.clear_sidebar_if_no_image()
                return
            else:
                await Message("Usage: /goto <checkpoint_number>").send()
                return
        except ValueError:
            await Message("Usage: /goto <checkpoint_number> (number must be an integer)").send()
            return
        except Exception as e:
            error_message = f"Error jumping to checkpoint: {str(e)}"
            print(error_message)
            await Message(error_message).send()

            # Always show traceback for this command to help with debugging
            import traceback
            print(f"Exception in /goto command: {str(e)}")
            print(traceback.format_exc())
            return

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
            message += "\nDu hast die **zentrale Frage** richtig beantwortet!\n\n"

        # Display the solution image only if it exists
        if iterations.image_solution():
            message_solution_image = Message("Hier siehst du eine Zusammenfassung der Lösung.")
            message_solution_image.image = iterations.image_solution()
            await message_solution_image.send(to_sidebar=True)

        # Always display the main answer text, but only if we're not coming from a guiding question
        if not understanding.guiding_question_answered:
            message += "Hier ist die Musterantwort der zentralen Frage: \n"
            message += iterations.main_answer()
        message += "\n\nLass uns mit der nächsten Aufgabe fortfahren.\n"
        await message.send()

        # Load next checkpoint and send it properly with image
        checkpoint_message = iterations.load_next_checkpoint()
        await checkpoint_message.send()

        # Clear sidebar if the new checkpoint has no solution image
        await iterations.clear_sidebar_if_no_image()
    elif understanding.guiding_question_answered or not iterations.has_step_iterations_left():
        ## moving to the next guiding question
        if state["debugging"]:
            message += f"**System**: Moving to the next guiding question.\n"
        if understanding.guiding_question_answered:
            message += "\nDu hast die Frage richtig beantwortet!\n\n"
        message += "Hier ist die Musterantwort dieser Frage: \n"
        # Get the answer for the step we just completed
        current_answer = iterations.guiding_answer()
        message += current_answer
        await message.send()
        # Check if we need to advance to next checkpoint
        if not iterations.has_checkpoint_iterations_left():
            # Handle checkpoint advancement
            checkpoint_message = iterations.load_next_checkpoint()
            await checkpoint_message.send()
        else:
            # Handle regular step with potential image
            step_message = iterations.load_next_step()
            await step_message.send()
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
