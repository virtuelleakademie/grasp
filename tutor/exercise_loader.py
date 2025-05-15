import yaml
import json
import os
from typing import Dict, Union, Any

from tutor.exercise_model import Exercise

class ExerciseLoader:
    @staticmethod
    def from_yaml(file_path: str) -> Exercise:
        """Load an exercise from a YAML file."""
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return Exercise.model_validate(data)

    @staticmethod
    def from_json(file_path: str) -> Exercise:
        """Load an exercise from a JSON file."""
        with open(file_path, 'r') as file:
            data = json.load(file)
        return Exercise.model_validate(data)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Exercise:
        """Create an exercise from a Python dictionary."""
        return Exercise.model_validate(data)

    @staticmethod
    def from_legacy_format(
        first_message: str,
        end_message: str,
        main_question: Dict[int, str],
        main_answer: Dict[int, str],
        guiding_questions: Dict[int, Dict[int, str]],
        guiding_answers: Dict[int, Dict[int, str]],
        image: Dict[int, Dict[int, Union[str, None]]],
        image_solution: Dict[int, Union[str, None]],
        metadata: Dict[str, Any] = None
    ) -> Exercise:
        """Convert legacy format to the new Exercise model."""
        if metadata is None:
            metadata = {
                "title": "ANOVA Exercise",
                "topic": "ANOVA",
                "level": "beginner",
                "language": "de",
                "author": "Legacy System",
                "tags": ["ANOVA", "F-Test"],
                "version": "1.0"
            }

        # Create checkpoints from legacy data
        checkpoints = []
        for cp_num in sorted(main_question.keys()):
            steps = []
            for step_num in sorted(guiding_questions.get(cp_num, {}).keys()):
                step = Step(
                    step_number=step_num,
                    guiding_question=guiding_questions[cp_num][step_num],
                    guiding_answer=guiding_answers[cp_num].get(step_num, ""),
                    image=image.get(cp_num, {}).get(step_num)
                )
                steps.append(step)

            checkpoint = Checkpoint(
                checkpoint_number=cp_num,
                main_question=main_question[cp_num],
                main_answer=main_answer[cp_num],
                image_solution=image_solution.get(cp_num),
                steps=steps
            )
            checkpoints.append(checkpoint)

        # Create the full exercise
        exercise = Exercise(
            metadata=ExerciseMetadata(**metadata),
            first_message=first_message,
            end_message=end_message,
            checkpoints=checkpoints
        )

        return exercise
