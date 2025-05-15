from typing import List
import json
from pydantic import BaseModel, Field



class ThoughtStep(BaseModel):
    step: int = Field(..., description="The index of the reasoning step, starting from 1")
    reasoning: str = Field(..., description="Thoughprocess for this step")
    intermediate_result: str = Field(..., description="Outcome or result of this reasoning step")


class BasicOutput(BaseModel):
    """
    Template class for structured output from the tutor agent.
    """
    chain_of_thought: List[ThoughtStep] = Field(
        ..., 
        description="List of individual reasoning steps that lead to determine the content for the remaining fields",
    )
#    each subclass should add a fitting OUtput type, such as:
#    final_answer: str = Field(..., description="The final result of the chain of thought")
    prompt: str = Field(..., description="empty string") # dummy placeholder used to show prompt in debugging

    def view_chain_of_thought(self) -> str:
        message = "\n".join(
            f"{step.step}. {step.reasoning}"
            + (f" → {step.intermediate_result}" if step.intermediate_result else "")
            for step in self.chain_of_thought
        )
        return message

    def view_prompt(self) -> str:
        message = f"""

**System**: I will generate a message for the following prompt:

{self.prompt}


"""
        return message

class Summary(BaseModel):
    summary: str = Field(..., description="A one-sentence summary of the user's understanding regarding a particular concept.")

class Understanding(BasicOutput):
    """
    Class for structured output from the tutor agent tasked to validate the user's understanding.
    """
    guiding_question_answered: bool = Field(..., description="Whether the guiding question was answered correctly.")
    main_question_answered: bool = Field(..., description="Whether the main question was answered.")
    summary: List[Summary] = Field(
        ..., 
        description="A bulletpoint summary of the user's understanding regarding the major concepts in full explanation of, both, main and guiding question, based on chain of thought.",
    )
    
    def context(self) -> str:
        """ 
        Create context for the tutor agent that contains the following:
        - the current understanding of the user
        """
        fields = self.model_dump()  ## dict of all fields
        fields.pop("chain_of_thought", None)  ## remove cot for context prompt
        fields.pop("prompt", None)  ## remove cot for context prompt
        understanding_json_string = json.dumps(fields, indent=2)
        return f"""\
### Current Understanding of User
This a summary of the current understanding of the user:
{understanding_json_string}

"""
    
    @classmethod
    def empty(cls) -> "Understanding":
        """Initialize an empty understanding."""
        return Understanding(
            guiding_question_answered=False,
            main_question_answered=False,
            summary=[
                Summary(summary=""),
                Summary(summary="")
            ],
            chain_of_thought=[
                ThoughtStep(step=1, reasoning="", intermediate_result=""),
                ThoughtStep(step=2, reasoning="", intermediate_result="")
            ],
            prompt=""
        )
   

class Feedback(BasicOutput):
    """
    Class for structured output from the tutor agent tasked to provide feedback.
    """
    feedback: str = Field(..., description="The feedback provided to the user, based on chain of thought.")

    @classmethod
    def empty(cls) -> "Feedback":
        return Feedback(
            prompt="",
            chain_of_thought=[
                ThoughtStep(step=1, reasoning="", intermediate_result=""),
                ThoughtStep(step=2, reasoning="", intermediate_result="")
            ],
            feedback="Could not create Feedback.",
        )

class Instructions(BasicOutput):
    """
    Class for structured output from the tutor agent tasked to provide instructions.
    """
    instructions: str = Field(..., description="The instruction provided to the user, based on chain of thought.")

    @classmethod
    def empty(cls) -> "Instructions":
        return Instructions(
            prompt="",
            chain_of_thought=[
                ThoughtStep(step=1, reasoning="", intermediate_result=""),
                ThoughtStep(step=2, reasoning="", intermediate_result="")
            ],
            instructions="Could not create Instructions.",
        )
