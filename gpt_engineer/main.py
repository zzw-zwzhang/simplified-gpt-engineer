import json
import typer
from pathlib import Path

from gpt_engineer.db import DB, DBs
from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.steps import STEPS, Config as StepsConfig

app = typer.Typer()


@app.command()
def main(
    project_path: str = typer.Argument("projects/markdown_editor", help="path"),
    model: str = typer.Argument("gpt-4", help="model id string"),
    temperature: float = 0.1,
    steps_config: StepsConfig = typer.Option(
        StepsConfig.SIMPLE, "--steps", "-s", help="decide which steps to run"
    ),
):

    model = fallback_model(model)
    ai = AI(
        model=model,
        temperature=temperature,
    )

    input_path = Path(project_path).absolute()
    workspace_path = input_path / "workspace"
    dbs = DBs(
        input=DB(input_path),
        workspace=DB(workspace_path),
        preprompts=DB(Path(__file__).parent / "preprompts"),
        logs=DB(input_path / "logs"),
    )

    steps = STEPS[steps_config]
    for step in steps:
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = json.dumps(messages)


if __name__ == "__main__":
    app()
