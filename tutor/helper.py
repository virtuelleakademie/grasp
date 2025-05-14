import functools
import chainlit as cl


## Decorator to inject agent state into the function's keyword arguments
def with_agent_state(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        state = cl.user_session.get("agent_state", {})
        try:
            # Inject 'state' into the function's keyword arguments
            return func(*args, state=state, **kwargs)
        finally:
            cl.user_session.set("agent_state", state)
    return wrapper