#!/usr/bin/env python3
"""
Example script for generating an exercise using the ExerciseGenerator.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path to import from grasp modules
sys.path.append(str(Path(__file__).parent.parent))

from grasp.tutor.exercise_generator import generate_exercise

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Generate a simple ANOVA exercise
    prompt = "Generate an ANOVA exercise for beginners in statistics. Include clear explanations and guided steps."
    
    # You could also specify a markdown file with additional content
    # markdown_file = "resources/statistics/anova_concepts.md"
    
    exercise = generate_exercise(prompt)
    
    # Print the generated exercise as JSON
    print(json.dumps(exercise.model_dump(), indent=2))
    
    # You could also save it to a file
    # with open("generated_exercise.json", "w") as f:
    #     json.dump(exercise.model_dump(), f, indent=2)

if __name__ == "__main__":
    main()