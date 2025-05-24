from pydantic_ai import Agent, RunContext
from tutor.models.responses import Understanding
from tutor.models.context import TutorContext
from tutor.agents.base_agent import create_base_agent

UNDERSTANDING_SYSTEM_PROMPT = """
You are a statistical tutor evaluating student understanding.

Your task is to analyze student responses and determine:
1. Whether they have answered the current guiding question
2. Whether they have answered the main question  
3. Their level of understanding and any misconceptions

Guidelines:
- Be generous with partial understanding
- Focus on core concepts rather than perfect explanations
- Identify specific misconceptions for targeted feedback
- Consider the student's learning progression
- The guiding question is considered answered if the user shows understanding of the key concept
- The main question is considered answered if the user arrived at the final conclusion
- Don't be too critical over minor errors or gaps, as long as the main concept is understood
"""

understanding_agent = create_base_agent(
    output_type=Understanding,
    system_prompt=UNDERSTANDING_SYSTEM_PROMPT
)

@understanding_agent.system_prompt
def get_understanding_prompt(ctx: RunContext[TutorContext]) -> str:
    """Dynamic system prompt based on current context"""
    return f"""
    {UNDERSTANDING_SYSTEM_PROMPT}
    
    Current Context:
    - Exercise: {ctx.deps.exercise.metadata.title}
    - Checkpoint {ctx.deps.current_checkpoint}: {ctx.deps.current_main_question}
    - Step {ctx.deps.current_step}: {ctx.deps.current_guiding_question}
    - Iteration: {ctx.deps.iterations.step_interactions}/{ctx.deps.max_step_iterations}
    
    Main Question and Full Answer:
    {ctx.deps.current_main_question}
    
    Answer: {ctx.deps.current_main_answer}
    
    Current Guiding Question and Full Answer:
    {ctx.deps.current_guiding_question}
    
    Answer: {ctx.deps.current_guiding_answer}
    
    Previous Understanding:
    {ctx.deps.current_understanding.summary_text()}
    
    Analyze the student's response and determine their understanding level.
    """

@understanding_agent.tool
def get_reference_answer(ctx: RunContext[TutorContext]) -> str:
    """Tool to access reference answers for comparison"""
    if ctx.deps.has_next_step():
        return ctx.deps.current_guiding_answer
    return ctx.deps.current_main_answer