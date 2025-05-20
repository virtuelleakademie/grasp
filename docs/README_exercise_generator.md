# Exercise Generator

This module provides functionality to generate structured educational exercises using OpenAI's structured output capability.

## Features

- Generate complete exercises with checkpoints, steps, and guiding questions
- Incorporate content from markdown files as reference materials
- Return structured Exercise objects compatible with the rest of the system
- Simple API for both programmatic and command-line usage
- Automatic loading of environment variables from `.env` file

## Setup

1. Make sure you have the required dependencies installed:
   ```
   pip install openai python-dotenv pydantic
   ```

2. Create a `.env` file in your project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage Examples

### Basic Programmatic Usage

```python
from grasp.tutor.exercise_generator import generate_exercise

# Load environment variables and generate a simple exercise
exercise = generate_exercise(
    "Generate an ANOVA exercise for beginners in statistics."
)

# Save to file
import json
with open("generated_exercise.json", "w") as f:
    json.dump(exercise.model_dump(), f, indent=2)
```

### With Markdown Reference Content

```python
from grasp.tutor.exercise_generator import generate_exercise

# Generate an exercise based on specific content
exercise = generate_exercise(
    "Generate an exercise based on this content about ANOVA",
    markdown_file="resources/statistics/anova_concepts.md"
)
```

### Using the ExerciseGenerator Class

```python
from grasp.tutor.exercise_generator import ExerciseGenerator

# Create a generator with custom settings
# Environment variables will be loaded automatically
generator = ExerciseGenerator(model="gpt-4.1")

# Generate multiple exercises
exercise1 = generator.generate("Create a beginner ANOVA exercise in English")
exercise2 = generator.generate("Create an advanced ANOVA exercise with interaction effects")
```

### Command-Line Usage

```bash
# Basic usage
python -m grasp.tutor.exercise_generator "Generate an ANOVA exercise for statistics students" --output exercise.json

# With markdown reference
python -m grasp.tutor.exercise_generator "Generate an exercise based on this content" --markdown resources/anova.md --output exercise.yaml

# Specify model
python -m grasp.tutor.exercise_generator "Generate a regression exercise" --model gpt-4.1 --output exercise.json
```

## Integration with Exercise Loader

The generated exercises are compatible with the existing `ExerciseLoader` class:

```python
from grasp.tutor.exercise_generator import generate_exercise
from grasp.tutor.exercise_loader import ExerciseLoader
import json

# Generate an exercise
exercise = generate_exercise("Generate a beginner ANOVA exercise")

# Save to file
with open("generated_exercise.json", "w") as f:
    json.dump(exercise.model_dump(), f, indent=2)

# Later, load the exercise
loaded_exercise = ExerciseLoader.load("generated_exercise.json")
```

## Environment Variables

The module uses `python-dotenv` to automatically load environment variables from a `.env` file. The following environment variables are used:

- `OPENAI_API_KEY`: Your OpenAI API key (required unless provided directly to the function/class)

## API Reference

### generate_exercise()

```python
def generate_exercise(
    prompt: str,
    markdown_file: Optional[str] = None,
    model: str = "gpt-4.1",
    api_key: Optional[str] = None
) -> Exercise
```

A simplified function to generate exercises without instantiating the ExerciseGenerator class.

### ExerciseGenerator class

```python
class ExerciseGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1")
    def generate(self, prompt: str, markdown_file: Optional[str] = None) -> Exercise
```

A class for generating exercises using OpenAI's structured output capability.
