# app_tutor.py
import os
import sys
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

mode = os.getenv("TUTOR_MODE") ## set in .env file. set to None to randomize mode
if mode:
    mode = mode.lower()
    if mode not in VALID_MODES:
        raise SystemExit(
            f"Error: Invalid tutor mode '{mode}'. Valid modes are: {', '.join(VALID_MODES)}"
        )
else:
    mode = random.choice(VALID_MODES)


#mode = VALID_MODES[0]  # force socratic
#mode = VALID_MODES[1]  # force instructional

print(f"Starting tutor agent in {mode} mode.")

# Load the exercise file - can be specified through environment variable or use default
default_exercise = "grasp/exercises/anova.yaml"
exercise_path = os.getenv("EXERCISE_PATH", default_exercise)
exercise = None

# Create exercises directory if it doesn't exist
os.makedirs(os.path.dirname(exercise_path), exist_ok=True)

try:
    # Attempt to load the exercise file
    exercise = ExerciseLoader.load(exercise_path)
    print(f"Loaded exercise: {exercise.metadata.title}")
except FileNotFoundError as e:
    print(f"Exercise file not found: {e}")
    print("Falling back to direct imports from exercises.py")
except Exception as e:
    print(f"Error loading exercise file: {e}")
    print("Falling back to direct imports from exercises.py")

@cl.on_chat_start
async def start():
    cl.user_session.set("agent_state", {
        "messages": [],
        "log": LogContainer(tutor_mode=mode, user="johndoe@bfh.ch"),
        "tutor_mode": mode,
        "current_checkpoint": 0,
        "current_step": 0,
        "iterations": Iterations(exercise) if exercise else Iterations(),  # Pass the exercise if loaded
        "exercise": exercise,  # Store the exercise in the state
        "current_understanding": Understanding.empty(),  # start with empty understanding
        "debugging": debug,
        "show_prompts": show_prompts or debug,
        "show_reasoning": show_reasoning or debug,
    })

    await starting_message()

@cl.on_message
async def route_chat(message: cl.Message):
    await chat(message)
