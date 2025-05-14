# app_tutor.py
import os, sys, random

import chainlit as cl

from agents.tutor.agent import chat, starting_message, Iterations
from agents.tutor.output_structure import Understanding
from agents.tutor.logging import LogContainer


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

@cl.on_chat_start
async def start():
#    cl.user_session.set("agent_mode", "instruction")
    cl.user_session.set("agent_state", {
        "messages": [],
        "log" : LogContainer(tutor_mode=mode, user="johndoe@bfh.ch"),
        "tutor_mode": mode,
        "current_checkpoint": 0,
        "current_step": 0,
        "iterations": Iterations(),
        "current_understanding": Understanding.empty(),  # start with empty understanding
        "debugging": debug,
        "show_prompts": show_prompts or debug,
        "show_reasoning": show_reasoning or debug,
        })
    
    await starting_message()

@cl.on_message
async def route_chat(message: cl.Message):
    await chat(message)
