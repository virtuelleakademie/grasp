from pydantic_ai import Agent, RunContext
from tutor.models.responses import Instructions
from tutor.models.context import TutorContext
from tutor.agents.base_agent import create_base_agent

INSTRUCTION_SYSTEM_PROMPT = """
You are a statistical tutor providing guidance to help students discover answers.

STRICT RULES - NEVER BREAK THESE:
- NEVER provide direct answers or explanations
- NEVER give examples, analogies, or metaphors
- NEVER reveal any part of the correct answer
- NEVER ask students to perform calculations
- NEVER introduce concepts beyond the current scope
- NEVER repeat information already given

Your instructions should:
1. Ask ONE focused question to guide thinking
2. Help students reflect on what they already know
3. Direct attention to specific aspects of the current question
4. Encourage the student to think step by step

Your task is to enable the user to answer the current guiding question according to your tutor mode.
Write a single, brief instruction that helps the student think about the question.
"""

instruction_agent = create_base_agent(
    output_type=Instructions,
    system_prompt=INSTRUCTION_SYSTEM_PROMPT
)

@instruction_agent.system_prompt
def get_instruction_prompt(ctx: RunContext[TutorContext]) -> str:
    """Dynamic system prompt based on current context and tutor mode"""
    
    mode_instructions = get_mode_specific_instructions(ctx.deps.tutor_mode)
    
    return f"""
    {INSTRUCTION_SYSTEM_PROMPT}
    
    Current Context:
    - Exercise: {ctx.deps.exercise.metadata.title}
    - Checkpoint {ctx.deps.current_checkpoint}: {ctx.deps.current_main_question}
    - Step {ctx.deps.current_step}: {ctx.deps.current_guiding_question}
    - Tutor Mode: {ctx.deps.tutor_mode}
    
    {mode_instructions}
    
    Main Question and Full Answer:
    {ctx.deps.current_main_question}
    
    Answer: {ctx.deps.current_main_answer}
    
    Current Guiding Question and Full Answer:
    {ctx.deps.current_guiding_question}
    
    Answer: {ctx.deps.current_guiding_answer}
    
    Current Understanding:
    - Main question answered: {ctx.deps.current_understanding.main_question_answered}
    - Guiding question answered: {ctx.deps.current_understanding.guiding_question_answered}
    - Summary: {ctx.deps.current_understanding.summary_text()}
    
    Generate helpful instructions that guide the student toward understanding.
    """

def get_mode_specific_instructions(mode: str) -> str:
    """Get tutor mode specific instructions"""
    if mode == "socratic":
        return """
        Socratic Mode Instructions:
        - ONLY ask questions, never give explanations or examples
        - Never provide analogies, metaphors, or examples
        - Ask ONE simple question at a time
        - Guide the student to think about the specific concept in the current question
        - If student is confused, ask what specific part they don't understand
        - Never give away any part of the answer
        - Help students identify their own misconceptions through questioning
        - Ask the user to explain concepts in their own words
        """
    elif mode == "instructional":
        return """
        Instructional Mode Instructions:
        - Provide clear explanations of concepts
        - Use examples to illustrate abstract ideas
        - Break down complex topics into steps
        - Help students apply concepts to specific problems
        - Give abstract explanation of the concept using technical terms
        - Help understand terms and provide guidance on application to specific problems
        - Provide instructions to correct mistakes when attempts are not correct
        """
    return ""

@instruction_agent.tool
def get_step_context(ctx: RunContext[TutorContext]) -> str:
    """Get context about current step progression"""
    return f"""
    Current step: {ctx.deps.current_step}
    Step iterations: {ctx.deps.iterations.step_interactions}/{ctx.deps.max_step_iterations}
    Checkpoint iterations: {ctx.deps.iterations.checkpoint_interactions}/{ctx.deps.max_checkpoint_iterations}
    Has next step: {ctx.deps.has_next_step()}
    Has next checkpoint: {ctx.deps.has_next_checkpoint()}
    """