# GRASP - Guided Reasoning Assistant for Statistics Practice

Welcome to GRASP, a framework for structured statistics tutoring exercises. This document explains how exercises are formatted, loaded, and used in the tutoring system.

## Overview

GRASP combines a structured exercise format with an intelligent tutoring system to provide guided learning experiences for statistics concepts. The system supports:

- Multiple tutoring modes (Socratic, Instructional)
- Structured progression through complex concepts
- Guided questioning with feedback
- Rich content with Markdown and LaTeX math
- Optional image support

## Exercise Format

Each GRASP exercise consists of:

- **Metadata**: Information about the exercise (title, topic, difficulty level, etc.)
- **First Message**: An introduction to the exercise
- **End Message**: A concluding message
- **Checkpoints**: Sequential learning points, each containing:
  - A main question
  - Its answer
  - An optional solution image
  - Multiple sequential **Steps** (guiding questions), each with:
    - A question
    - An answer
    - An optional image

### Example YAML Format

```yaml
metadata:
  title: "Introduction to ANOVA"
  topic: "ANOVA"
  level: "beginner"
  language: "en"
  author: "John Doe"
  tags: ["ANOVA", "F-Test", "Statistics"]

first_message: "Today we'll explore Analysis of Variance (ANOVA)..."

end_message: "Great job! You've completed this exercise."

checkpoints:
  - checkpoint_number: 1
    main_question: "How do we compare means across multiple groups?"
    main_answer: "We use ANOVA to compare means across multiple groups..."
    image_solution: "static/solution_image.png"
    steps:
      - step_number: 1
        guiding_question: "What is the null hypothesis in ANOVA?"
        guiding_answer: "The null hypothesis in ANOVA states that all group means are equal..."
        image: "static/step1_image.png"
```

## Tutoring System

The GRASP tutoring system guides students through exercises with a combination of AI components:

### Tutor Modes

The system supports different tutoring approaches:

1. **Socratic Mode**: Asks questions to guide the student toward understanding, without directly providing answers.
2. **Instructional Mode**: Provides explanations of concepts using technical terms, then helps the student apply them.

The mode can be specified in environment variables or randomly assigned:

```python
mode = os.getenv("TUTOR_MODE")  # Set in .env file or randomize if None
```

### Key Components

#### Iterations Class

The `Iterations` class manages progression through an exercise:

- Tracks current checkpoint and step
- Provides access to questions, answers, and images
- Manages transitions between steps and checkpoints

#### Message Handling

The system uses a `Message` class to format and send content to the user:

- Supports text messages with markdown and LaTeX
- Handles image attachments
- Provides concatenation operations for building complex messages

#### Reasoning Components

Three main reasoning components evaluate and respond to student input:

1. **TutorCheckUnderstanding**: Evaluates if the student has answered the questions
   ```python
   understanding = await check_understanding(user_input)
   ```

2. **TutorFeedback**: Provides constructive feedback on responses
   ```python
   feedback = await generate_feedback(user_input)
   ```

3. **TutorInstructions**: Generates questions or hints to guide learning
   ```python
   instructions = await generate_instructions(user_input)
   ```

## Loading and Generating Exercises

### Loading Existing Exercises

Exercises are loaded from YAML or JSON files using the `ExerciseLoader`:

```python
from grasp.tutor.exercise_loader import ExerciseLoader

# Load from a file (detects format from extension)
exercise = ExerciseLoader.load("path/to/exercise.yaml")

# Explicitly load from specific format
exercise = ExerciseLoader.from_yaml("path/to/exercise.yaml")
exercise = ExerciseLoader.from_json("path/to/exercise.json")

# Load from a dictionary
data = {...}  # Dictionary matching Exercise structure
exercise = ExerciseLoader.from_dict(data)
```

The app automatically looks for exercises in the specified path or falls back to a default:

```python
default_exercise = "grasp/exercises/anova.yaml"
exercise_path = os.getenv("EXERCISE_PATH", default_exercise)
```

### Generating New Exercises

The `ExerciseGenerator` module automates the creation of new exercises:

```python
from grasp.tutor.exercise_generator import ExerciseGenerator

# Initialize with optional custom settings
generator = ExerciseGenerator(model="gpt-4o")

# Generate an exercise
exercise = generator.generate(
    "Create a beginner ANOVA exercise that explains F-tests"
)

# Generate with reference material
exercise = generator.generate(
    "Create an exercise on statistical power analysis",
    markdown_file="resources/statistics/power_analysis.md"
)
```

See the `grasp/tutor/README_exercise_generator.md` for complete documentation.

## Generating Exercises

GRASP provides an `ExerciseGenerator` module that simplifies the creation of exercises using OpenAI's structured output:

```python
from grasp.tutor.exercise_generator import generate_exercise

# Generate a simple exercise
exercise = generate_exercise(
    "Generate an ANOVA exercise for beginners in statistics."
)

# With markdown content as reference
exercise = generate_exercise(
    "Generate an exercise based on this content",
    markdown_file="resources/statistics/anova_concepts.md"
)

# Save to file
import json
with open("generated_exercise.json", "w") as f:
    json.dump(exercise.model_dump(), f, indent=2)
```

The generator also supports command-line usage:

```bash
# Basic usage
python -m grasp.tutor.exercise_generator "Generate an ANOVA exercise" --output exercise.json

# With markdown reference
python -m grasp.tutor.exercise_generator "Generate an exercise" --markdown resources/anova.md
```

### Using Directly with LLMs

The exercise format can also be used directly with LLM structured output:

```python
from openai import OpenAI
from grasp.tutor.exercise_model import Exercise

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Generate an ANOVA exercise..." }],
    response_format={"type": "pydantic_model", "schema": Exercise.model_json_schema()}
)

exercise = response.choices[0].message.parsed
```

## Tutor Interaction Flow

The tutoring process follows this general flow:

1. The system presents the first message and main question
2. For each checkpoint:
   - The system presents guiding questions one by one
   - For each guiding question:
     - The system checks the student's understanding
     - Provides feedback on their answers
     - Gives instructions or hints to improve understanding
   - Once all guiding questions are answered, the system presents the main question again
3. After all checkpoints are completed, the system shows the end message

## Content Guidelines

When creating exercises:

- All text supports **Markdown and LaTeX** (using `$...$` for math)
- Steps must be **sequentially numbered** (starting from 1)
- Images are **optional**, specified via relative path or URL
- Each checkpoint should have **at least one guiding step**
- Include a complete metadata block in all files

## Key Features

- YAML & JSON supported for input/output
- Human and AI authoring capabilities
- Automated exercise generation with OpenAI
- Reference material integration from Markdown files
- Rich content with Markdown and LaTeX math
- Optional image support
- Extensible metadata
- Strong validation via Pydantic

For complete details on the exercise format, see `grasp/docs/specifications/exercise_requirements.md`.
For documentation on exercise generation, see `grasp/tutor/README_exercise_generator.md`.
