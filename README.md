# GRASP - Guided Reasoning Assistant for Statistics Practice

Welcome to GRASP, a framework for structured statistics tutoring exercises. This document explains how exercises are formatted, loaded, and used in the tutoring system.


## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/virtuelleakademie/grasp.git
cd grasp
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your OpenAI API key

Create a `.env` file in the root of your project with the following content:

```env
OPENAI_API_KEY=your-openai-api-key
```

You can get your key at: https://platform.openai.com/account/api-keys

---


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

## Loading Exercises

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

## Using with LLMs

The exercise format is designed to work well with LLM structured output:

```python
from openai import OpenAI
from grasp.tutor.exercise_model import Exercise

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    input=[{"role": "user", "content": "Generate an ANOVA exercise..." }],
    text_format=Exercise
)

exercise = response.output_parsed
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
- Rich content with Markdown and LaTeX math
- Optional image support
- Extensible metadata
- Strong validation via Pydantic

For complete details on the exercise format, see `grasp/docs/specifications/exercise_requirements.md`.
