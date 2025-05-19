# app_tutor.py
import os
import random

import chainlit as cl

from tutor.agent import chat, starting_message, Iterations
from tutor.output_structure import Understanding
from tutor.logging import LogContainer
from tutor.exercise_loader import ExerciseLoader


debug = False  # Set to True to see all system messages
show_prompts = False  # Set to True to see the prompts used in the agent
show_reasoning = False  # Set to True to see the reasoning of the agent

VALID_MODES = ['socratic', 'instructional']

print(f"Starting tutor agent application.")

# Set default directory and exercise file
DEFAULT_EXERCISE_DIR = "exercises"
DEFAULT_EXERCISE_FILE = "t-test.yaml"

# Check for environment variable, otherwise use default
exercise_path = os.getenv("EXERCISE_PATH")
if not exercise_path:
    # If no EXERCISE_PATH is specified, use the default directory and file
    exercise_path = os.path.join(DEFAULT_EXERCISE_DIR, DEFAULT_EXERCISE_FILE)
    print(f"No EXERCISE_PATH specified. Using default: {exercise_path}")
else:
    print(f"Using exercise path from environment: {exercise_path}")

# Create exercises directory if it doesn't exist (only needed if using default)
if not os.getenv("EXERCISE_PATH"):
    os.makedirs(DEFAULT_EXERCISE_DIR, exist_ok=True)

exercise = None
try:
    # Attempt to load the exercise file
    exercise = ExerciseLoader.load(exercise_path)
    print(f"Loaded exercise: {exercise.metadata.title}")
except FileNotFoundError as e:
    print(f"Exercise file not found: {exercise_path}")
    print("Falling back to direct imports from exercises.py")
except Exception as e:
    print(f"Error loading exercise file: {e}")
    print("Falling back to direct imports from exercises.py")

@cl.on_chat_start
async def start():
    # Initialize with None
    tutor_mode = None
    user_id = "anonymous"

    # STEP 1: Try to get user_id from available sources
    # Check authenticated user if available
    if hasattr(cl, 'user_session') and hasattr(cl.user_session, 'user') and cl.user_session.user:
        user = cl.user_session.user
        if hasattr(user, 'identifier') and user.identifier:
            user_id = user.identifier

            # If user is authenticated, try to get mode from user metadata
            if hasattr(user, 'metadata') and user.metadata and 'tutor_mode' in user.metadata:
                candidate_mode = user.metadata.get('tutor_mode', '').lower()
                if candidate_mode in VALID_MODES:
                    tutor_mode = candidate_mode
                    print(f"Using tutor mode '{tutor_mode}' from user metadata for user {user_id}")

    # STEP 2: If still no valid mode, try HTTP headers via context
    if not tutor_mode and hasattr(cl, 'context'):
        # Try to get from headers (lowercased by convention)
        headers = cl.context.get('headers', {})
        candidate_mode = headers.get('x-tutor-mode', '').lower()
        if candidate_mode in VALID_MODES:
            tutor_mode = candidate_mode
            print(f"Using tutor mode '{tutor_mode}' from HTTP header for user {user_id}")

        # If user_id is still default, try to get from headers too
        if user_id == "anonymous" and 'x-user-id' in headers:
            user_id = headers.get('x-user-id')

    # STEP 3: If still no valid mode, try query parameters
    if not tutor_mode and hasattr(cl, 'context'):
        query_params = cl.context.get('query_params', {})
        if 'mode' in query_params:
            candidate_mode = query_params.get('mode', '').lower()
            if candidate_mode in VALID_MODES:
                tutor_mode = candidate_mode
                print(f"Using tutor mode '{tutor_mode}' from query parameters for user {user_id}")

        # If user_id is still default, try to get from query params too
        if user_id == "anonymous" and 'user_id' in query_params:
            user_id = query_params.get('user_id')

    # STEP 4: Fallback to random mode if all else fails
    if not tutor_mode:
        tutor_mode = random.choice(VALID_MODES)
        print(f"No valid tutor mode found for user {user_id}. Using random mode: {tutor_mode}")

    print(f"Session initialized for user {user_id} with tutor mode: {tutor_mode}")

    # Initialize the session with determined values
    cl.user_session.set("agent_state", {
        "messages": [],
        "log": LogContainer(tutor_mode=tutor_mode, user=user_id),
        "tutor_mode": tutor_mode,
        "current_checkpoint": 0,
        "current_step": 0,
        "iterations": Iterations(exercise) if exercise else Iterations(),
        "exercise": exercise,
        "current_understanding": Understanding.empty(),
        "debugging": debug,
        "show_prompts": show_prompts or debug,
        "show_reasoning": show_reasoning or debug,
    })

    await starting_message()

@cl.on_message
async def route_chat(message: cl.Message):
    await chat(message)
