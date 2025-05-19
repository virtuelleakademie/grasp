import yaml
import json
import os
from typing import Dict, Any, List, Union
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
            Exercise: A validated Exercise instance with adjusted paths
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

            # Get the exercise directory to adjust relative paths
            exercise_dir = os.path.dirname(file_path)
            data = ExerciseLoader._adjust_paths(data, exercise_dir)

            return Exercise.model_validate(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in exercise file: {e}")

    @staticmethod
    def from_json(file_path: str) -> Exercise:
        """Load an exercise from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Exercise: A validated Exercise instance with adjusted paths
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Get the exercise directory to adjust relative paths
            exercise_dir = os.path.dirname(file_path)
            data = ExerciseLoader._adjust_paths(data, exercise_dir)

            return Exercise.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in exercise file: {e}")

    @staticmethod
    def from_dict(data: Dict[str, Any], base_dir: str = None) -> Exercise:
        """Create an exercise from a Python dictionary.

        Args:
            data: Dictionary containing exercise data
            base_dir: Optional base directory to adjust relative paths

        Returns:
            Exercise: A validated Exercise instance
        """
        if base_dir:
            data = ExerciseLoader._adjust_paths(data, base_dir)
        return Exercise.model_validate(data)

    @staticmethod
    def _adjust_paths(data: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
        """Adjust all paths in the exercise data to be relative to the application root.

        This recursively processes the dictionary to find any image paths and adjusts them.

        Args:
            data: Exercise data dictionary
            base_dir: Base directory of the exercise bundle

        Returns:
            Updated dictionary with adjusted paths
        """
        if not data:
            return data

        # Path fields that need adjustment
        image_fields = ["image", "image_solution"]

        # Create a deep copy to avoid modifying the original
        result = data.copy()

        # Process fields directly in the main data structure
        for field in image_fields:
            if field in result and result[field] and isinstance(result[field], str):
                if not os.path.isabs(result[field]):  # Only adjust relative paths
                    result[field] = os.path.join(base_dir, result[field])

        # Process checkpoints
        if "checkpoints" in result and isinstance(result["checkpoints"], list):
            for i, checkpoint in enumerate(result["checkpoints"]):
                if isinstance(checkpoint, dict):
                    # Adjust checkpoint images
                    for field in image_fields:
                        if field in checkpoint and checkpoint[field] and isinstance(checkpoint[field], str):
                            if not os.path.isabs(checkpoint[field]):
                                result["checkpoints"][i][field] = os.path.join(base_dir, checkpoint[field])

                    # Process steps within checkpoints
                    if "steps" in checkpoint and isinstance(checkpoint["steps"], list):
                        for j, step in enumerate(checkpoint["steps"]):
                            if isinstance(step, dict) and "image" in step and step["image"] and isinstance(step["image"], str):
                                if not os.path.isabs(step["image"]):
                                    result["checkpoints"][i]["steps"][j]["image"] = os.path.join(base_dir, step["image"])

        return result
