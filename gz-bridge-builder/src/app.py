from pathlib import Path
import typer
from typing_extensions import Annotated

from gz_bridge_builder import core

app = typer.Typer(
    name="gz-bridge-builder",
    help="A utility to generate ros_gz_bridge YAML files from URDF.",
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
            help="Path to save the generated bridge YAML file. Defaults to 'bridge.yaml' in the current directory.",
            resolve_path=True,
        ),
    ] = Path("bridge.yaml"),
):
    """
    Generates a ros_gz_bridge YAML file by parsing <bridge> tags in a URDF file.
    """
    try:
        typer.echo(f"Parsing URDF file: {urdf_path}")
        root = core.parse_urdf(urdf_path)
        
        bridge_elements = core.extract_bridge_tags(root)
        if not bridge_elements:
            typer.echo("No <bridge> tags found in the URDF file. Exiting.")
            raise typer.Exit(code=0)

        bridges = [core.parse_bridge_tag(elem) for elem in bridge_elements]
        
        yaml_content = core.generate_bridge_yaml(bridges)
        
        output_path.write_text(yaml_content)
        typer.echo(f"Successfully generated bridge YAML to: {output_path}")

    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}", err=True)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
