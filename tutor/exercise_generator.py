import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI
from dotenv import load_dotenv

from tutor.exercise_model import Exercise, ExerciseMetadata, Checkpoint, Step

class ExerciseGenerator:
    """
    A class for generating exercises using OpenAI's structured output capability.

    This class allows for:
    - Generation of exercises based on text prompts
    - Incorporation of content from markdown files
    - Returning structured Exercise objects compatible with the rest of the system

    Examples:
        # Basic usage
        generator = ExerciseGenerator()
        exercise = generator.generate("Create a beginner ANOVA exercise in English")

        # With markdown content
        exercise = generator.generate(
            "Create an exercise based on this content",
            markdown_file="resources/statistics/anova_concepts.md"
        )
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1"):
        """
        Initialize the exercise generator.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY environment variable
            model: OpenAI model to use (default: "gpt-4.1")
        """
        # Load environment variables from .env file
        load_dotenv()
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, prompt: str, markdown_file: Optional[str] = None) -> Exercise:
        """
        Generate an exercise based on a prompt and optional markdown content.

        Args:
            prompt: The instruction for generating the exercise
            markdown_file: Optional path to a markdown file with additional content

        Returns:
            A validated Exercise object
        """
        messages = self._build_messages(prompt, markdown_file)

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=messages,
                text_format=Exercise,
                temperature=0.2
            )

            return response.output_parsed

        except Exception as e:
            raise RuntimeError(f"Error generating exercise: {str(e)}")

    def _build_messages(self, prompt: str, markdown_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Build the message list for the API call, including markdown content if provided."""
        content = prompt

        if markdown_file:
            md_path = Path(markdown_file)
            if not md_path.exists():
                raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            content = f"{prompt}\n\nUse the following content as reference:\n\n{markdown_content}"

        system_message = (
            "You are an expert educational content creator specializing in creating interactive exercises. "
            "Generate a well-structured exercise that follows best practices in instructional design. "
            "Make the exercise coherent, educational, and aligned with the provided content."
        )

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": content}
        ]



def generate_exercise(
    prompt: str,
    markdown_file: Optional[str] = None,
    model: str = "gpt-4.1-mini",
    api_key: Optional[str] = None
) -> Exercise:
    """
    A simplified function to generate exercises without instantiating the ExerciseGenerator class.

    Args:
        prompt: The instruction for generating the exercise
        markdown_file: Optional path to a markdown file with additional content
        model: OpenAI model to use (default: "gpt-4.1")
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY environment variable

    Returns:
        A validated Exercise object

    Example:
        exercise = generate_exercise(
            "Generate an ANOVA exercise for statistics students",
            markdown_file="resources/statistics/anova_concepts.md"
        )
    """
    print(f"Initializing exercise generator with model: {model}")
    generator = ExerciseGenerator(api_key=api_key, model=model)

    print(f"Starting exercise generation based on prompt:\n{prompt[:100]}...")
    if markdown_file:
        print(f"Using additional content from: {markdown_file}")

    return generator.generate(prompt, markdown_file)

def save_exercise(exercise, base_filename=None, formats=None, exercise_dir=None):
    """
    Save an exercise to file(s) in specified format(s).

    Args:
        exercise: The Exercise object to save
        base_filename: Base filename without extension (default: 'generated_exercise')
        formats: List of formats to save in ('json', 'yaml', or both) (default: ['json'])
        exercise_dir: Directory to save files in (default: 'exercises/generated-exercises')

    Returns:
        Dictionary of {format: filepath} for each successfully saved format
    """
    import os
    import json

    # Set defaults
    base_filename = base_filename or "generated_exercise"
    formats = formats or ["json"]
    exercise_dir = exercise_dir or "examples/generated-exercises"

    # Ensure directory exists
    os.makedirs(exercise_dir, exist_ok=True)

    # Prepare exercise data
    exercise_data = exercise.model_dump()

    saved_files = {}

    # Handle each format
    for fmt in formats:
        filepath = os.path.join(exercise_dir, f"{base_filename}.{fmt}")

        try:
            if fmt.lower() == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(exercise_data, f, indent=2)
                saved_files["json"] = filepath

            elif fmt.lower() in ["yaml", "yml"]:
                try:
                    import yaml
                    with open(filepath, "w", encoding="utf-8") as f:
                        yaml.dump(exercise_data, f, sort_keys=False, indent=2)
                    saved_files["yaml"] = filepath
                except ImportError:
                    print("PyYAML is not installed. Skipping YAML output.")

        except Exception as e:
            print(f"Error saving {fmt} file: {e}")

    # Report results
    for fmt, path in saved_files.items():
        print(f"Exercise saved in {fmt.upper()} format to: {path}")

    return saved_files


if __name__ == "__main__":
    import argparse
    import json
    import yaml

    # Ensure environment variables are loaded
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate educational exercises using OpenAI")
    parser.add_argument("prompt", help="Prompt for generating the exercise")
    parser.add_argument("--markdown", "-m", help="Path to markdown file with additional content")
    parser.add_argument("--output", "-o", help="Output file path (without extension)")
    parser.add_argument("--model", default="gpt-4.1", help="OpenAI model to use (default: gpt-4.1)")
    parser.add_argument("--formats", "-f", nargs="+", choices=["json", "yaml"],
                        default=["json"], help="Output formats (default: json)")
    parser.add_argument("--output-dir", "-d", default="exercises/generated-exercises",
                        help="Directory to save output files (default: exercises/generated-exercises)")
    args = parser.parse_args()

    exercise = generate_exercise(args.prompt, args.markdown, args.model)

    if args.output:
        # Use the save_exercise function with the provided parameters
        save_exercise(
            exercise,
            base_filename=args.output,
            formats=args.formats,
            exercise_dir=args.output_dir
        )
    else:
        # Just print to stdout
        print(json.dumps(exercise.model_dump(), indent=2))
