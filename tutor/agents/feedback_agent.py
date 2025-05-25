from pydantic_ai import Agent, RunContext
from tutor.models.responses import Feedback
from tutor.models.context import TutorContext
from tutor.agents.base_agent import create_base_agent

FEEDBACK_SYSTEM_PROMPT = """
You are a supportive statistical tutor providing constructive feedback.

Your feedback should:
1. Start with positive acknowledgment of understanding
2. Address specific misconceptions or gaps
3. Encourage continued learning
4. Never reveal answers directly

Guidelines:
- Acknowledge and summarize the student's understanding using bullet points
- Highlight where the user clearly improved their understanding
- Provide constructive feedback pointing out mistakes, gaps or misunderstandings
- Never mention any terms in the full explanation the user has not yet used
- Never add any additional technical terms
- Never ask questions (these will be posed by someone else)
- Focus on the current guiding question unless it's answered, then acknowledge briefly
"""

feedback_agent = create_base_agent(
    output_type=Feedback,
    system_prompt=FEEDBACK_SYSTEM_PROMPT
)

@feedback_agent.system_prompt
def get_feedback_prompt(ctx: RunContext[TutorContext]) -> str:
    """Dynamic system prompt based on current context and tutor mode"""
    
    mode_instructions = get_mode_instructions(ctx.deps.tutor_mode)
    
    return f"""
    {FEEDBACK_SYSTEM_PROMPT}
    
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
    
    Provide constructive feedback following your guidelines and tutor mode.
    """

def get_mode_instructions(mode: str) -> str:
    """Get tutor mode specific instructions for feedback"""
    if mode == "socratic":
        return """
        Socratic Mode - Feedback Guidelines:
        - Use questions to guide discovery in your feedback
        - Help students identify their own misconceptions
        - Encourage critical thinking through guided reflection
        - Build understanding through questioning approach
        """
    elif mode == "instructional":
        return """
        Instructional Mode - Feedback Guidelines:  
        - Provide clear explanations of concepts in your feedback
        - Use examples to illustrate abstract ideas
        - Break down complex topics into steps
        - Help students apply concepts to specific problems
        """
    return ""

@feedback_agent.tool
def get_conversation_context(ctx: RunContext[TutorContext]) -> str:
    """Get recent conversation history for context"""
    recent_messages = ctx.deps.conversation_history[-3:] if ctx.deps.conversation_history else []
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])