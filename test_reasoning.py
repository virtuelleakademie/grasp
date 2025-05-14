
from agents.tutor.reasoning import TutorCheckUnderstanding
from agents.tutor.agent import Iterations

if __name__ == "__main__":
    # for testing purposes
    import asyncio
    import chainlit as cl
    cl.user_session.set("agent_state", {
        "messages": [],
        "tutor_mode": "instruction",
        "current_checkpoint": 0,
        "current_step": 0,
        "iterations": Iterations(),
        })
    tutor = TutorCheckUnderstanding()
    user_input = "user_input"
    understanding = asyncio.run(tutor.check_understanding(user_input))
    print(understanding.chain_of_thought)
    print(understanding.main_question_answered)
    print(understanding.guiding_question_answered)
    for s in understanding.summary:
        print(s)

