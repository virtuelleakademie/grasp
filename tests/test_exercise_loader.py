# grasp/tests/test_exercise_loader.py
import pytest
import os
import tempfile
import yaml
import json
import sys
from pathlib import Path

# Add the project root to Python's module search path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now imports will work
from grasp.tutor.exercise_loader import ExerciseLoader
from grasp.tutor.exercise_model import Exercise, ExerciseMetadata, Checkpoint, Step


# Get the path to the test directory
TEST_DIR = Path(__file__).parent
# Get the path to the project root directory
PROJECT_ROOT = TEST_DIR.parent
# Path to the example exercises
EXERCISES_DIR = PROJECT_ROOT / "exercises"

class TestExerciseLoader:
    def test_load_yaml_file(self):
        """Test loading an existing YAML exercise."""
        # Use an existing exercise file
        exercise_path = EXERCISES_DIR / "anova.yaml"

        # Make sure the file exists before testing
        assert exercise_path.exists(), f"Test file not found: {exercise_path}"

        # Load the exercise
        exercise = ExerciseLoader.load(str(exercise_path))

        # Basic validation
        assert isinstance(exercise, Exercise)
        assert exercise.metadata.title == "Einführung in die Varianzanalyse"
        assert exercise.metadata.topic == "ANOVA"
        assert len(exercise.checkpoints) > 0

    def test_load_with_relative_path(self):
        """Test loading with a relative path from the test directory."""
        # Using a relative path from the current test file
        relative_path = "../exercises/anova.yaml"

        # Load the exercise
        exercise = ExerciseLoader.load(str(TEST_DIR / relative_path))

        # Validate
        assert isinstance(exercise, Exercise)
        assert exercise.metadata.title == "Einführung in die Varianzanalyse"

    def test_load_nonexistent_file(self):
        """Test handling of nonexistent files."""
        with pytest.raises(FileNotFoundError):
            ExerciseLoader.load("nonexistent_file.yaml")

    def test_load_invalid_extension(self):
        """Test handling of invalid file extensions."""
        # Create a temporary file with an invalid extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"dummy content")
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError):
                ExerciseLoader.load(tmp_path)
        finally:
            os.unlink(tmp_path)  # Clean up

    def test_create_and_load_yaml(self):
        """Test creating a YAML file and loading it."""
        # Create a temporary YAML file
        exercise_data = {
            "metadata": {
                "title": "Test Exercise",
                "topic": "Testing",
                "level": "beginner",
                "language": "en"
            },
            "first_message": "Welcome to the test exercise!",
            "end_message": "You completed the test exercise!",
            "checkpoints": [{
                "checkpoint_number": 1,
                "main_question": "What is testing?",
                "main_answer": "Testing verifies that code works as expected.",
                "steps": [{
                    "step_number": 1,
                    "guiding_question": "Why test?",
                    "guiding_answer": "To catch bugs early."
                }]
            }]
        }

        # Create a named temporary file but close it immediately
        temp_file = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False)
        temp_file.close()

        try:
            # Write to the file with text mode
            with open(temp_file.name, 'w', encoding='utf-8') as file:
                yaml.dump(exercise_data, file)

            # Load the exercise
            exercise = ExerciseLoader.load(temp_file.name)

            # Verify the exercise
            assert isinstance(exercise, Exercise)
            assert exercise.metadata.title == "Test Exercise"
            assert exercise.metadata.language == "en"
            assert len(exercise.checkpoints) == 1
        finally:
            # Clean up
            os.unlink(temp_file.name)


    def test_from_dict(self):
        """Test creating an exercise from a dictionary."""
        # Create sample data
        data = {
            "metadata": {
                "title": "Dictionary Exercise",
                "topic": "Testing",
                "language": "en"
            },
            "first_message": "Welcome!",
            "end_message": "Goodbye!",
            "checkpoints": [{
                "checkpoint_number": 1,
                "main_question": "Question?",
                "main_answer": "Answer.",
                "steps": [{
                    "step_number": 1,
                    "guiding_question": "Guide?",
                    "guiding_answer": "Response."
                }]
            }]
        }

        # Create exercise from dictionary
        exercise = ExerciseLoader.from_dict(data)

        # Verify
        assert exercise.metadata.title == "Dictionary Exercise"
        assert len(exercise.checkpoints) == 1
        assert exercise.checkpoints[0].steps[0].guiding_question == "Guide?"



# This allows running this file directly
if __name__ == "__main__":
    test_main()
