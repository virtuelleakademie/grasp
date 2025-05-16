# Exercise Generator

This module provides functionality to generate structured educational exercises using OpenAI's structured output capability.

## Features

- Generate complete exercises with checkpoints, steps, and guiding questions
- Incorporate content from markdown files as reference materials
- Return structured Exercise objects compatible with the rest of the system
- Simple API for both programmatic and command-line usage

## Usage Examples

### Basic Programmatic Usage

```python
from grasp.tutor.exercise_generator import generate_exercise

# Generate a simple exercise
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
generator = ExerciseGenerator(model="gpt-4o")

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
python -m grasp.tutor.exercise_generator "Generate a regression exercise" --model gpt-4o --output exercise.json
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

## API Reference

### generate_exercise()

```python
def generate_exercise(
    prompt: str, 
    markdown_file: Optional[str] = None,
    model: str = "gpt-4o",
    api_key: Optional[str] = None
) -> Exercise
```

A simplified function to generate exercises without instantiating the ExerciseGenerator class.

### ExerciseGenerator class

```python
class ExerciseGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o")
    def generate(self, prompt: str, markdown_file: Optional[str] = None) -> Exercise
```

A class for generating exercises using OpenAI's structured output capability.