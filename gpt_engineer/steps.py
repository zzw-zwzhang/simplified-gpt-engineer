import re
import json
import inspect
import subprocess
from enum import Enum
from typing import List
from termcolor import colored

from gpt_engineer.ai import AI
from gpt_engineer.db import DBs
from gpt_engineer.chat_to_files import to_files


def setup_sys_prompt(dbs: DBs) -> str:
    return (
        dbs.preprompts["generate"] + "\nUseful to know:\n" + dbs.preprompts["philosophy"]
    )


def curr_fn() -> str:
    """Get the name of the current function"""
    return inspect.stack()[1].function


def simple_gen(ai: AI, dbs: DBs) -> List[dict]:
    """Run the AI on the main prompt and save the results"""
    system_content = setup_sys_prompt(dbs)
    user_content = dbs.input["prompt"]
    
    messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
    ]
    
    responses = ai.next(messages, step_name=curr_fn())
    
    to_files(responses[-1]["content"], dbs.workspace)
    return responses



def gen_entrypoint(ai: AI, dbs: DBs) -> List[dict]:
    system_content = dbs.preprompts["generate_entrypoint"]
    user_content = "Information about the codebase:\n\n" + dbs.workspace["all_output.txt"]
    
    messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
    ]
    
    responses = ai.next(messages, step_name=curr_fn())
    
    print()
    regex = r"```\S*\n(.+?)```"
    matches = re.finditer(regex, responses[-1]["content"], re.DOTALL)
    dbs.workspace["run.sh"] = "\n".join(match.group(1) for match in matches)
    
    return responses


def execute_entrypoint(ai: AI, dbs: DBs) -> List[dict]:
    command = dbs.workspace["run.sh"]
    print(command)

    print("Do you want to execute this code?")
    print()
    print(command)
    print()
    print('If yes, press enter. Otherwise, type "no"')
    print()
    if input() not in ["", "y", "yes"]:
        print("Ok, not executing the code.")
        return []
    print("Executing the code...")
    print()
    print(
        colored(
            "Note: If it does not work as expected, consider running the code"
            + " in another way than above.",
            "green",
        )
    )
    print()
    print("You can press ctrl+c *once* to stop the execution.")
    print()

    p = subprocess.Popen("bash run.sh", shell=True, cwd=dbs.workspace.path)
    try:
        p.wait()
    except KeyboardInterrupt:
        print()
        print("Stopping execution.")
        print("Execution stopped.")
        p.kill()
        print()

    return []


class Config(str, Enum):
    SIMPLE = "simple"


# Different configs of what steps to run
STEPS = {
    Config.SIMPLE: [simple_gen, gen_entrypoint, execute_entrypoint],
}
