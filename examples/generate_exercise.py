#!/usr/bin/env python3
"""
Example script for generating an exercise using the ExerciseGenerator.
"""

# %%
import os
import sys
import json
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# Add the parent directory to the path to import from grasp modules
sys.path.append(str(Path(__file__).parent.parent))

from tutor.exercise_generator import generate_exercise
from tutor.exercise_generator import save_exercise

# %%
def main():
    # Load environment variables from .env file
    load_dotenv()

    # Generate a simple ANOVA exercise
    prompt = """
    Generate a repeated-measures ANOVA exercise for beginners
    in statistics. Include clear explanations, guided steps and figures.
    """

    # Specify a markdown file with additional content
    markdown_file = "assets/markdown/repeated-measures-anova.md"

    exercise = generate_exercise(prompt, markdown_file=markdown_file)

    # Print the generated exercise as JSON
    print(json.dumps(exercise.model_dump(), indent=2))

    save_exercise(exercise, formats=["json", "yaml"])

if __name__ == "__main__":
    main()
