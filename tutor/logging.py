import os

from datetime import datetime
import json

from tutor.output_structure import Understanding


class LogContainer:
    def __init__(self, tutor_mode: str = None, user: str = None):
        self.log = {
            "tutor_mode": tutor_mode,
            "user": user,
            "messages": [],
        }
        self.old_file = None
        self.write_to_file = False  ## set to True to write log file after each update

    def append(self, message_dict, write=True) -> None:
        """add user message to log"""
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        message_dict["timestamp"] = time
        self.log["messages"].append(message_dict)
        if self.write_to_file and write:
            self.to_file(time)

    def append_reasoning(self, llm_output) -> None:
        """ add to log the reasoning of LLMs """
        message_dict = {
            "prompt": llm_output.prompt,
            "chain_of_thought": llm_output.view_chain_of_thought()
        }
        if isinstance(llm_output, Understanding):
            message_dict["inferred student understanding"] = llm_output.context()
        self.append(message_dict)

    def append_system_message(self, message: str) -> None:
        self.log["messages"].append(message)

    def to_file(self, time) -> None:
        """ writes the current log to file """
        # Ensure the directory exists before writing the file
        filename = self.filename(time)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w") as f:
            json.dump(self.log, f, indent=2)

        try:
            # check file is written correctly
            with open(filename, "r") as f:
                data = json.load(f)

            # if file is good, remove old file
            if data == self.log and os.path.isfile(self.old_file):
                os.remove(self.old_file)
        except:
            pass

    def filename(self, time):
        return f"logs/tutor/{self.log['user']}_{time}.json"
