import yaml
import json
import os
from typing import Dict, Any
from pathlib import Path

from grasp.tutor.exercise_model import Exercise

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
        """Load an exercise from a file, automatically detecting format from file extension.

        Args:
            file_path: Path to the YAML or JSON file containing exercise data

        Returns:
            Exercise: A validated Exercise instance

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file extension is not supported (.yaml, .yml, or .json)
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Exercise file not found: {file_path}")

        extension = path.suffix.lower()

        if extension in ('.yaml', '.yml'):
            return ExerciseLoader.from_yaml(file_path)
        elif extension == '.json':
            return ExerciseLoader.from_json(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {extension}. Use .yaml, .yml, or .json")

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
