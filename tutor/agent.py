import time

import chainlit as cl

from tutor.exercises import main_question, main_answer, guiding_questions, image, image_solution, guiding_answers, first_message, end_message
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
            await cl.AskUserMessage(content=end_message, timeout=10).send()
#            await cl.Message(content=end_message).send()
#            time.sleep(10)
        return

    @with_agent_state
    async def send_image(self, to_sidebar: bool = True, state=None) -> None:
        """Send an image."""
        it = state["iterations"]
        element = cl.Image(name=f"Visual Q{it.current_checkpoint} S{it.current_step}", path=self.image)
#        if to_sidebar:  ## always to both, message and sidebar
        await cl.ElementSidebar.set_elements([element])
        await cl.ElementSidebar.set_title("Checkpoint Image")
#        else:
        await cl.Message(content="", elements=[element]).send()
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
    def __init__(self) -> None:
        self.total = 0
        self.step = 0
        self.checkpoint = 0
        self.max_step = max_interactions_step  ## Maximum number of interactions per guiding question
        self.max_checkpoint = max_interactions_checkpoint ## Maximum number of interactions before moving on to the next checkpoint
        self.current_step = 0
        self.current_checkpoint = 0
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
            return main_question[self.current_checkpoint]
        except IndexError:
            raise IndexError("No more checkpoints available.")

    def main_answer(self) -> str:
        """Get the main answer for the current checkpoint."""
        return main_answer[self.current_checkpoint]

    def image(self) -> str:
        """Get the image path for the current checkpoint."""
        return image[self.current_checkpoint][self.current_step]

    def image_solution(self) -> str:
        """Get the image solution path for the current checkpoint."""
        return image_solution[self.current_checkpoint]


    def guiding_question(self) -> str:
        """Get the guiding question for the current checkpoint and step."""
        try:
            question = guiding_questions[self.current_checkpoint][self.current_step]
        except:
            question = "All guiding questions have been answered."
        return question

    def guiding_answer(self) -> str:
        """Get the guiding answer for the current checkpoint and step."""
        try:
            answer = guiding_answers[self.current_checkpoint][self.current_step]
        except:
            answer = ""
        return answer

    @with_agent_state
    def load_next_step(self, state=None) -> str:
        """Load the next instruction or advance to the next checkpoint if no iterations are left."""
        # continue with next checkpoint if no iterations are left
        message = Message("")
        if not self.has_checkpoint_iterations_left():
            if state["debugging"]:
                print(f"System: No more iterations left for Checkpoint {self.current_checkpoint}.")
#            message += "Let's move on to the next checkpoint.\n"
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
            message += f"\n\nLass uns {"zuerst" if self.current_step == 1 else "jetzt"} über diese Frage nachdenken:\n"
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
#            message.image = self.image()
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
    message = Message(f"""
Gruezi! Ich bin heute dein Tutor für Statistik.

{first_message}

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

        if image_solution[iterations.current_checkpoint]:
            message_solution_image = Message("Hier siehst du eine Zusammenfassung der Lösung.")
            message_solution_image.image = image_solution[iterations.current_checkpoint]
            await message_solution_image.send(to_sidebar=True)

        message += "Dass hier ist die Musterantwort der zentralen Frage: \n"
        message += iterations.main_answer()
        message += "\n\nLass ins mit der nächsten Aufgabe fortfahren.\n"
        await message.send()
        message = Message("")
        message += iterations.load_next_checkpoint()
    elif understanding.guiding_question_answered or not iterations.has_step_iterations_left():
        ## moving to the next guiding question
        if state["debugging"]:
            message += f"**System**: Moving to the next guiding question.\n"
        if understanding.guiding_question_answered:
            message += "\nDu hast die Frage richtig beantwortet!\n\n"
        message += "Dass hier ist die Musterantwort dieser Frage: \n"
        message += iterations.guiding_answer()
        await message.send()
        message = Message("")
        message += iterations.load_next_step()
    else:
        ## continue with the same guiding question
        if state["debugging"]:
            message += f"**System**: Continuing with the same guiding question.\n"
#        message += "\n\nLet's try again.\n"
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
'''
    # Placeholder for actual instructions generation logic.
    return Instructions(
        chain_of_thought="cot",
        instruction = f"Instructions based on: {user_input}"
    )
'''

tutor_feedback = TutorFeedback()
async def generate_feedback(user_input: str) -> Feedback:
    """Generate feedback based on user input."""
    feedback = await tutor_feedback.generate_feedback(user_input)
    return feedback
'''
    # Placeholder for actual feedback generation logic.
    return Feedback(
        chain_of_thought="cot",
        feedback = f"Feedback based on: {user_input}"
    )
'''

tutor_check = TutorCheckUnderstanding()
async def check_understanding(user_input: str) -> Understanding:
    """Check if the user understands the concept."""
    understanding = await tutor_check.check_understanding(user_input)
    return understanding
''''
    # Placeholder for actual understanding check logic.
    return Understanding(
        chain_of_thought="cot",
        main_question_answered=main_question_answered(user_input),
        guiding_question_answered=guiding_question_answered(user_input),
        summary=["summarized unterstanding"])
'''
