import os
import pprint

from openai import OpenAI
from pydantic import BaseModel

from tutor.helper import with_agent_state
from tutor.output_structure import BasicOutput, Understanding, Feedback, Instructions

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


"""
ToDo
- create test for check_understanding: list of answers with target *_question_answered
- work on Problems in LLM Reasoning


Problems in Reasoning:

- to check guiding question, he requires knowledge from the main question -> clearly separate
- gives feedback on why main question is not answered, as though user tried to anser, when only guide question is answered


instructional
- gives away the connection (crossed lines indicate interaction, meaning one variable affects the other) -> should only give explanation (interaction, meaning ....), then help make the connection
"""


@with_agent_state
def llm_structured(messages, models=["gpt-4o-mini", "gpt-4o", "o3-mini"], temperature=0.5, top_p=0.5, response_format=None, state=None):
    """
    Create a new instance of the OpenAI model with the specified parameters.
    """
    if state["debugging"]:
        pprint.pprint(messages)

    if state["iterations"].finished:
        return response_format.empty()

    for model in models:
        try:
            print(f"Try {model}")
            output = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                temperature=temperature if model != "o3-mini" else None,
                top_p=top_p,
                response_format=response_format,
                timeout=5,
            ).choices[0].message.parsed
            return output
        except Exception as e:
            warning = f"**WARNING** Model {model} failed with error: {e}"
            print(warning)
            state["log"].append_system_message(warning)
            continue
    output = response_format.empty()

    return output

class TutorBasic:
    """
    Basic tutor class for generating sophisticated interactions with students.
    This class is designed as a unified base for tutor agents with different modes and styles
    """

    @with_agent_state
    async def generate_message(self, content: list, temperature=0.5, top_p=0.5, response_format: BaseModel = BasicOutput, state=None) -> str:
        """
        Generate a message based on last user input in content list.
        """
        output = llm_structured(content, temperature=temperature, top_p=top_p, response_format=response_format)
        output.prompt = ( # for logging, safe the prompt in output. when debug or show_prompt set to True, prompt is shown in chat window
            f"# System prompt:\n" + content[0]["content"] + "\n\n"
            f"# User prompt:\n" + content[-1]["content"][0]["text"]
        )
        state["log"].append_reasoning(output)
        return output




    @with_agent_state
    def content(self, user_input: str, state=None) -> list:
        """
        Generate the full content for the tutor agent.
        """
        content = [
            {
                "role": "system",
                "content": self.system_prompt()
            }
        ]
        content.extend(state["messages"][-3:])
        content.extend([
            {
                "role": "user",
                "content": [{"type": "text", "text": self.user_prompt(user_input)}]
            }
        ])
        return content


    @with_agent_state
    def system_prompt(self, state=None) -> dict:
        """
        Create a system prompt to frame the tutor agent.
        """
        prompt =  f"""\
# Statistical Tutor

## General Task
You are a helpful assistant designed to assist students in understanding complex concepts.
Your goal is to help the user to understand the concept and to answer the main question
by first answering the guiding question.

## Session Description
You are shown a dialogue between a student (`user`) and a tutor (`assistant`).

## Meta Instruction Handling
The final `user` message is not from the student, but an external instruction.
It defines your task for analyzing or acting on the preceding conversation.

## General Instructions
- you speak German, unless instructed otherwise
- never give away information from the full explanations of questions, unless the user mentioned them. Instead, guide the user to that understanding.
- never use technical terms that are not in context yet
- always focus your instructions on answering the guiding questions. Unless they are all answered, then focus on the main question
- in Feedback for a guiding question, don't mention any parts of the main question that have not been addressed yet.
- Never ask the user to calculate anything. Instead, when the user identified what needs to be computed, the question is considered to be answered.
- Never push ahead to knowledge beyond the current guiding question.

{self.special_tutor_instructions()}

## Language and Style
- You are a friendly and supportive tutor.
- Your language should be clear, concise, and encouraging.
"""

        return prompt

    @with_agent_state
    def special_tutor_instructions(self, state=None) -> str:
        """
        Special instructions for the tutor agent based on the tutor mode.
        """
        instructions = f"""## Tutor Mode Instructions
This defines the procedure of your tutor mode.
Follow these instructions **strictly** and **without exception**:
"""
        if state["tutor_mode"] == "instructional":
            # the instructional tutor gives an abstract explanation of the concept to be learned using technical terms
            # then helps the user to understand the concapt and apply to the specific problem by defining unknown terms and providing explanations and examples
            instructions += f"""
Your method of tutoring is instructional.
You strictly follow the following procedure:
1. After presenting a new question, you will provide an abstract explanation of the concept in question using technical terms, then ask the user if they understand the terms and to apply it to the specific problem at hand.
2. When the user asks questions, you will help to understand the terms as well as the abstract concept and provide guidance on how to apply it to the specific problem at hand.
3. When the user attempts an answer that is not correct, you will provide instructions to correct it.
4. When the user attempts an answer that is correct, you will provide encouraging feedback on their learning process.
"""
        elif state["tutor_mode"] == "socratic":
            instructions += f"""
Your tutoring style is Socratic.
You **strictly** follow the procedure below **without exception**:

1. After presenting the main question Start with a diagnosis question:
    - Ask the learner to state, in one sentence, what they currently believe to be the answer and what is most unclear.

2. In the following discussion — you provide **questions only**, no direct explanations
    - Restate each interim insight briefly, then ask the next question, either:
    - Reveal misconceptions: Give concrete examples that make the user see the misconception by probing consequences. E.g., "You assume that all numbers are even. What about if I take any even number, say 2, and add 1?”
    - Reveal gaps: Ask the user to explain the concept in their own words. E.g., "Can you explain the concept in your own words?"
"""
        return instructions

    def user_prompt(self, user_input: str) -> dict:
        """
        Create a prompt for specific instructions on the user input
        """
        return f"""\
## Instructions
{self.instructions()}

## User Input
{user_input}

## Context
{self.context()}
"""
    def instructions(self) -> str:
        """
        instructions for the tutor agent.
        This method should be overridden by subclasses to provide specific instructions.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def context(self) -> str:
        """
        Create a Context prompt for the tutor agent.
        This method should be overridden by subclasses to provide specific context.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @with_agent_state
    def context_full(self, state=None) -> str:
        """
        Create context for the tutor agent that contains the following:
        - the main and guiding question and answer
        - the current understanding of the user
        """
        prompt = f"""\
{self.context_question()}

{state["current_understanding"].context()}
"""
        return prompt


    @with_agent_state
    def context_question(self, state=None) -> str:
        """
        Create context for the tutor agent that contains the following:
        - the main and guiding question and answer
        """
        iterations = state["iterations"]
        prompt = f"""\
### Main Question
This is the main question to be answered:
{iterations.main_question()}

#### Full Answer
{iterations.main_answer()}

### Guiding Question
This is the current guiding question to be answered:
{iterations.guiding_question()}

#### Full Answer
{iterations.guiding_answer()}
"""
        return prompt









class TutorCheckUnderstanding(TutorBasic):
    """
    Tutor class to check the user's understanding of concepts
    """

    async def check_understanding(self, user_input: str) -> Understanding:
        """
        Check if the user shows understanding of the concept based on their response.
        """
        ## in the future, we will use the LLM to check the understanding of the user
        understanding = await self.generate_message(self.content(user_input), response_format=Understanding)
        '''
        ## this is dummy for testing, print the prompts in chat window
        prompts = await self.generate_message(self.content(user_input)) ## currently gives the prompts to be passed to the LLM
        understanding = Understanding(
                    chain_of_thought=prompts, ## put here to be plotted later
                    main_question_answered=main_question_answered(user_input),
                    guiding_question_answered=guiding_question_answered(user_input),
                    summary=["summarized unterstanding"])
        '''
        return understanding

    def instructions(self) -> str:
        """
        instructions for the tutor agent to check the user's understanding of concepts.
        """
        return f"""\
Your task is to check the user's understanding of the concept based on their response.
In particular:
- for both questions, main and guiding, individually evaluate whether they are answered by the user's response.
- the quetsions and Full Explanation are provided in the context.
- The guiding question is considered answered if the user shows understanding of the boldface concept and roughly explained it in their own words.
- The main question is considered answered if the user arrived at the final conclusion, shown in boldface, and roughly explained it in an abstract or concrete way.
- Don't be too critical over minor errors or gaps, as long as the main concept is understood.
- Do only consider the information in the full explanation to evaluate
- Below you are given the current understanding of the user, which should only be updated positively, improving the user's understanding.
"""

    context = TutorBasic.context_full

    def special_tutor_instructions(self, state=None) -> str:
        """
        No Special instructions for this tutor agent, just the general instructions,
        to ensure uniform behavior independant of tutor modes, required for experiments.
        """
        return ""





class TutorFeedback(TutorBasic):
    """
    Tutor class to provide feedback to the user based on their response.
    """

    context = TutorBasic.context_full

    def instructions(self):
        """
        instructions for the tutor agent to provide feedback to the user based on their response.
        """
        return f"""\
Your task is to provide feedback to the user based on their response.
1. start with a positive feedback: acknowledge and summarize concisely the understanding of the user using bullit points. If applicable, highlight where the user clearly improved their understanding.
2. if the guiding question is
  - not answered yet: in the form of observations, provide a constructive feedback, pointing out the mistakes, gaps or misunderstandings, if there are any, that the user showed in their response.
  - answered: very briefly acknowledge that
3. if some concept important for the main question has just been understood, acknowledge that shortly.

**strictly** satisfy these demands
- never mention any terms in the full explanation the user has not yet used.
- never add any additional technical terms
- never ask questions (these will be posed by someone else)

"""


    async def generate_feedback(self, user_input: str) -> Feedback:
        """
        Generate feedback based on user input.
        This method should be overridden by subclasses to provide specific feedback generation logic.
        """
        ## in the future, we will use the LLM to generate feedback for the user
        feedback = await self.generate_message(self.content(user_input), response_format=Feedback)
        '''
        ## this is dummy for testing, print the prompts in chat window
        prompts = await self.generate_message(self.content(user_input))
        feedback = Feedback(
                    chain_of_thought=prompts, ## put here to be plotted later
                    feedback="Feedback based on: " + user_input)
        '''
        return feedback

class TutorInstructions(TutorBasic):
    """
    Tutor class to provide instructions to the user based on their response.
    """
    context = TutorBasic.context_full

    def instructions(self):
        """
        instructions for the tutor agent to provide instructions to the user based on their response.
        """
        return f"""\
Your task is to enable the user to answer the current guiding question based, according to your tutor mode.
Write the single instruction that you think will help the user to answer the guiding question.

**Strictly follow these instructions without exception**:
- never give away any parts of the answer
- never ask to repeat any information that was already given.
- never ask the user to compute anything
"""

    async def generate_instructions(self, user_input: str) -> Instructions:
        """
        Generate instructions based on user input.
        This method should be overridden by subclasses to provide specific instruction generation logic.
        """
        ## in the future, we will use the LLM to generate instructions for the user
        instructions = await self.generate_message(self.content(user_input), response_format=Instructions)
        '''
        ## this is dummy for testing, print the prompts in chat window
        prompts = await self.generate_message(self.content(user_input))
        instructions = Instructions(
                    chain_of_thought=prompts, ## put here to be plotted later
                    instructions="Instructions based on: " + user_input)
        '''
        return instructions




## helpful functions for development and testing


def guiding_question_answered(s):
    return "answer" in s.lower()

def main_question_answered(s):
    return "concept" in s.lower()
