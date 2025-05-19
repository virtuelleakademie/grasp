# GRASP - Guided Reasoning Assistant for Statistics Practice

Welcome to GRASP, a framework for structured statistics tutoring exercises powered by AI. This document explains how to install, use, and extend the tutoring system, as well as how to create and manage exercises.

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/virtuelleakademie/grasp.git
cd grasp
```

### 2. Create and activate a virtual environment

```bash
# For Unix/macOS
python -m venv .venv
source .venv/bin/activate

# For Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your OpenAI API key

Create a `.env` file in the root directory with the following content:

```env
OPENAI_API_KEY=your-openai-api-key
```

You can get your key at: <https://platform.openai.com/account/api-keys>

---

## 🚀 Getting Started

### Running the Tutor

To start the GRASP tutoring system with the default exercise:

```bash
chainlit run app.py -w
```

You can specify a custom exercise, a tutoring mode, or a combination thereof.

**Exercise**:

```bash
EXERCISE_NAME=t-test chainlit run app.py -w
````

**Socratic tutoring mode**:

```bash
TUTOR_MODE=socratic chainlit run app.py -w
```

**Instructional tutor**:

```bash
TUTOR_MODE=instructional chainlit run app.py -w
```

**Exercise and tutoring mode**:

```bash
EXERCISE_NAME=t-test TUTOR_MODE=instructional chainlit run app.py -w
```

## 📋 Overview

GRASP combines a structured exercise format with an intelligent tutoring system to provide guided learning experiences for statistics concepts. The system supports:

- Multiple tutoring modes (Socratic, Instructional)
- Structured progression through complex concepts
- Guided questioning with feedback
- Rich content with Markdown and LaTeX math
- Optional image support
- Exercise generation with LLMs

## 📝 Exercise Format

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
  version: "1.0"
  date_created: "2023-10-15"

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

## 🧠 Tutoring System

GRASP's intelligent tutoring system guides students through exercises using a combination of AI components:

### Tutor Modes

The system supports different tutoring approaches that adapt to student needs:

1. **Socratic Mode**: Asks questions to guide the student toward understanding, without directly providing answers. This mode encourages critical thinking and self-discovery.

2. **Instructional Mode**: Provides detailed explanations of concepts using technical terms, then helps the student apply them. This mode is more directive and educational.

The mode can be specified in multiple ways:

- Environment variable: `TUTOR_MODE=socratic chainlit run app.py`
- URL query parameter: `http://localhost:8000/?mode=instructional`
- HTTP header: `X-Tutor-Mode: socratic`
- User metadata (when integrated with authentication)

If not specified, the system will randomly select a mode for each session.

### Key Components

#### Iterations Class

The `Iterations` class manages progression through an exercise:

- Tracks current checkpoint and step
- Provides access to questions, answers, and images
- Manages transitions between steps and checkpoints

#### Message Handling

The system uses a `Message` class to format and send content to the user:

- Supports rich text with Markdown and LaTeX math
- Handles image attachments with automatic rendering
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

## 📚 Working with Exercises

### Organizing Exercises

Exercises are organized into directories following this structure:

```
exercises/
├── t-test/                   # Exercise identifier/name
│   ├── exercise.yaml         # Main exercise definition
│   ├── figures/               # Optional directory for images
│   │   ├── step1.png
│   │   └── solution.png
│   └── resources/            # Optional additional resources
├── anova/
│   ├── exercise.yaml
│   └── ...
└── linear-regression/
    ├── exercise.json         # Can be JSON instead of YAML
    └── ...
```

### Loading Existing Exercises

Exercises are loaded from YAML or JSON files using the `ExerciseLoader`:

```python
from grasp.tutor.exercise_loader import ExerciseLoader

# Load from a file (detects format from extension)
exercise = ExerciseLoader.load("exercises/t-test/exercise.yaml")

# Explicitly load from specific format
exercise = ExerciseLoader.from_yaml("exercises/t-test/exercise.yaml")
exercise = ExerciseLoader.from_json("exercises/linear-regression/exercise.json")

# Load from a dictionary
data = {...}  # Dictionary matching Exercise structure
exercise = ExerciseLoader.from_dict(data)
```

The app automatically looks for exercises based on environment variables:

```python
# Default exercise directory and name
EXERCISES_DIR = "exercises"
EXERCISE_NAME = "t-test"

# Override with environment variables
EXERCISE_NAME=anova EXERCISES_DIR=custom_exercises python -m chainlit run app.py
```

### Generating New Exercises

The `ExerciseGenerator` module automates the creation of new exercises using OpenAI's GPT models:

```python
from grasp.tutor.exercise_generator import ExerciseGenerator

# Initialize with optional custom settings
generator = ExerciseGenerator(model="gpt-4.1")

# Generate a basic exercise
exercise = generator.generate(
    "Create a beginner ANOVA exercise that explains F-tests"
)

# Generate with reference material
exercise = generator.generate(
    "Create an exercise on statistical power analysis",
    markdown_file="resources/statistics/power_analysis.md"
)

# Save the generated exercise
from grasp.tutor.exercise_generator import save_exercise
save_exercise(exercise, base_filename="anova_f_test", formats=["json", "yaml"])
```

### Command-Line Exercise Generation

GRASP provides a convenient command-line interface for generating exercises:

```bash
# Basic usage
python -m grasp.tutor.exercise_generator "Generate an ANOVA exercise" --output anova_exercise

# With markdown reference material
python -m grasp.tutor.exercise_generator "Generate an exercise" --markdown resources/statistics/anova.md --output anova_exercise

# Specify output formats and directory
python -m grasp.tutor.exercise_generator "Generate a t-test exercise" --formats json yaml --output-dir exercises/t-test
```

### Using Directly with OpenAI API

The exercise format can also be used directly with the OpenAI API:

```python
from openai import OpenAI
from grasp.tutor.exercise_model import Exercise

client = OpenAI()

response = client.responses.parse(
    model="gpt-4.1-mini",
    input=[
        {"role": "user", "content": "Generate an ANOVA exercise..." }
    ],
    text_format=Exercise
)

exercise = response.output_parsed
```

## 🔄 Interaction Flow

The GRASP tutoring process follows this general flow:

1. **Introduction**: The system presents the first message introducing the topic
2. **Main Question**: The first checkpoint's main question is presented
3. **Guided Learning**: For each checkpoint:
   - The system presents guiding questions one by one
   - For each guiding question:
     - The system evaluates the student's understanding of the concept
     - Provides adaptive feedback on their answers
     - Gives further instructions or hints based on their progress
   - Once all guiding questions are answered, the system presents the main question again
4. **Progression**: After completing a checkpoint, the system proceeds to the next checkpoint
5. **Conclusion**: After all checkpoints are completed, the system shows the end message

## 📋 Content Guidelines

When creating exercises:

- All text supports **Markdown formatting and LaTeX** (using `$...$` for inline math and `$$...$$` for display math)
- Steps must be **sequentially numbered** (starting from 1)
- Checkpoints must be **sequentially numbered** (starting from 1)
- Images are **optional**, specified via relative path or URL
- Each checkpoint should have **at least one guiding step**
- Include a complete metadata block with all required fields
- Use clear, concise language appropriate for the specified difficulty level

## 🌟 Key Features

- **Multiple Formats**: YAML & JSON supported for exercise definition
- **Flexible Authoring**: Both human and AI authoring capabilities
- **AI Generation**: Automated exercise creation with OpenAI models
- **Reference Integration**: Incorporate existing material from Markdown files
- **Rich Content**: Full support for Markdown and LaTeX mathematical notation
- **Visual Support**: Optional image inclusion for each step and solution
- **Extensible Metadata**: Customizable properties for categorization and filtering
- **Strong Validation**: Type checking and validation via Pydantic
- **Multiple Tutoring Styles**: Socratic and instructional approaches

For complete details on the exercise format, see `grasp/docs/specifications/exercise_requirements.md`.
For comprehensive documentation on exercise generation, see `grasp/docs/README_exercise_generator.md`.
