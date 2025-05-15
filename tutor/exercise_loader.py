import yaml
import json
import os
from typing import Dict, Any
from pathlib import Path

from tutor.exercise_model import Exercise

class ExerciseLoader:
    """Utility class for loading Exercise objects from various sources.

    This class provides methods to load exercises from:
    - YAML files
    - JSON files
    - Python dictionaries

    Examples:
        # Load from a file (automatically detects format from extension)
        exercise = ExerciseLoader.load('exercises/calculus/derivatives.yaml')

        # Load from a specific format
        exercise = ExerciseLoader.from_json('exercises/statistics/anova.json')

        # Load from a dictionary
        data = {...}  # Dictionary matching Exercise structure
        exercise = ExerciseLoader.from_dict(data)
    """

    @staticmethod
    def load(file_path: str) -> Exercise:
        """Load an exercise from a file, automatically detecting format from file extension."""
        path = Path(file_path)
        extension = path.suffix.lower()

        # Check extension first
        if extension not in ('.yaml', '.yml', '.json'):
            raise ValueError(f"Unsupported file extension: {extension}. Use .yaml, .yml, or .json")

        # Then check if file exists
        if not path.exists():
            raise FileNotFoundError(f"Exercise file not found: {file_path}")

        if extension in ('.yaml', '.yml'):
            return ExerciseLoader.from_yaml(file_path)
        else:  # Must be .json at this point
            return ExerciseLoader.from_json(file_path)

    @staticmethod
    def from_yaml(file_path: str) -> Exercise:
        """Load an exercise from a YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Exercise: A validated Exercise instance
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            return Exercise.model_validate(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in exercise file: {e}")

    @staticmethod
    def from_json(file_path: str) -> Exercise:
        """Load an exercise from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Exercise: A validated Exercise instance
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return Exercise.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in exercise file: {e}")

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Exercise:
        """Create an exercise from a Python dictionary.

        Args:
            data: Dictionary containing exercise data

        Returns:
            Exercise: A validated Exercise instance
        """
        return Exercise.model_validate(data)
