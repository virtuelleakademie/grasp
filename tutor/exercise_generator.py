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

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the exercise generator.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY environment variable
            model: OpenAI model to use (default: "gpt-4o")
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
        model: OpenAI model to use (default: "gpt-4o")
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


if __name__ == "__main__":
    import argparse
    import json
    import yaml

    # Ensure environment variables are loaded
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate educational exercises using OpenAI")
    parser.add_argument("prompt", help="Prompt for generating the exercise")
    parser.add_argument("--markdown", "-m", help="Path to markdown file with additional content")
    parser.add_argument("--output", "-o", help="Output file path (.json or .yaml)")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    args = parser.parse_args()

    exercise = generate_exercise(args.prompt, args.markdown, args.model)

    if args.output:
        output_path = Path(args.output)
        if output_path.suffix.lower() in ('.yaml', '.yml'):
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(exercise.model_dump(), f, sort_keys=False)
        else:  # Default to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(exercise.model_dump(), f, indent=2)
        print(f"Exercise saved to {args.output}")
    else:
        print(json.dumps(exercise.model_dump(), indent=2))
