from pathlib import Path
import typer
from typing import Optional
from typing_extensions import Annotated

from urdf_bridge_builder import core

app = typer.Typer(
    name="urdf-bridge-builder",
    help="A utility to generate ros_urdf_bridge YAML files from URDF.",
    pretty_exceptions_enable=False,
)

@app.command()
def generate(
    urdf_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Path to the URDF file containing <bridge> tags.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            "--output", "-o",
            help="Path to save the generated output. Defaults to 'bridge.yaml' for YAML, or prints to stdout for launch_params.",
            resolve_path=True,
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--format", "-f",
            help="Output format: 'yaml' (default) or 'launch_params'.",
            case_sensitive=False,
        ),
    ] = "yaml",
):
    """
    Generates bridge configuration by parsing <bridge> tags in a URDF file.
    Output can be YAML or a list of launch parameters for ros_gz_bridge.
    """
    try:
        typer.echo(f"Parsing URDF file: {urdf_path}")
        root = core.parse_urdf(urdf_path)
        
        bridge_elements = core.extract_bridge_tags(root)
        if not bridge_elements:
            typer.echo("No <bridge> tags found in the URDF file. Exiting.")
            raise typer.Exit(code=0)

        bridges = [core.parse_bridge_tag(elem) for elem in bridge_elements]
        
        if output_format == "yaml":
            content = core.generate_bridge_yaml(bridges)
            if output_path is None:
                output_path = Path("bridge.yaml")
            output_path.write_text(content)
            typer.echo(f"Successfully generated bridge YAML to: {output_path}")
        elif output_format == "launch_params":
            # For launch_params, generate a Python-style list of dicts.
            # Use repr() to get a string representation that can be directly used in a Python launch file.
            content = core.generate_launch_params(bridges)
            formatted_content = repr(content) 

            if output_path is None:
                typer.echo("Generated launch parameters:")
                typer.echo(formatted_content)
            else:
                output_path.write_text(formatted_content)
                typer.echo(f"Successfully generated launch parameters to: {output_path}")
        else:
            raise ValueError(f"Unknown output format: {output_format}. Expected 'yaml' or 'launch_params'.")

    except FileNotFoundError as e:
        typer.echo(f"Error: URDF file not found: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}", err=True)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
