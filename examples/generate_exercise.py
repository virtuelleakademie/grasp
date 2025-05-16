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


# %%
def main():
    # Load environment variables from .env file
    load_dotenv()

    # Generate a simple ANOVA exercise
    prompt = """
    Generate a repeated-measures ANOVA exercise for beginners
    in statistics. Include clear explanations and guided steps.
    """

    # Specify a markdown file with additional content
    markdown_file = "assets/markdown/repeated-measures-anova.md"

    exercise = generate_exercise(prompt, markdown_file=markdown_file)

    # Print the generated exercise as JSON
    print(json.dumps(exercise.model_dump(), indent=2))

    # You could also save it to a file
    with open("generated_exercise.json", "w") as f:
        json.dump(exercise.model_dump(), f, indent=2)

    # Save as YAML
    try:
        with open("generated_exercise.yaml", "w") as f:
            yaml.dump(exercise.model_dump(), f, indent=2)
        print("Exercise also saved to generated_exercise.yaml")
    except ImportError:
        print("PyYAML is not installed. Skipping YAML output.")
    except Exception as e:
        print(f"An error occurred while saving to YAML: {e}")

if __name__ == "__main__":
    main()
