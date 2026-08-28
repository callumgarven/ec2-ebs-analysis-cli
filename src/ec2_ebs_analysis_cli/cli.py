from typing import Annotated

import typer

from ec2_ebs_analysis_cli.aws import EC2Service
from ec2_ebs_analysis_cli.formatters import format_json, format_plaintext
from ec2_ebs_analysis_cli.models import EC2Instance, OutputFormat, SortField, SortOrder

app = typer.Typer(
    name="ec2-ebs-analysis-cli",
    help="CLI tool to gather and summarize EBS volumes attached to EC2 instances.",
    add_completion=False,
)


def sort_instances(
    instances: list[EC2Instance], sort_by: SortField, sort_order: SortOrder
) -> list[EC2Instance]:
    """Sort instance list client-side based on requested field and order."""
    reverse = sort_order == SortOrder.DESC

    if sort_by == SortField.EBS_SIZE:
        return sorted(instances, key=lambda x: x.total_ebs_gb, reverse=reverse)
    if sort_by == SortField.NAME:
        return sorted(instances, key=lambda x: x.name.lower(), reverse=reverse)
    if sort_by == SortField.STATE:
        return sorted(instances, key=lambda x: x.state.lower(), reverse=reverse)
    if sort_by == SortField.ID:
        return sorted(instances, key=lambda x: x.instance_id, reverse=reverse)

    return instances


@app.command()
def analyze(
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Filter instances by Name tag value (uses AWS server-side filter).",
        ),
    ] = None,
    region: Annotated[
        str,
        typer.Option(
            "--region",
            "-r",
            help="AWS region to query (defaults to AWS_DEFAULT_REGION or eu-west-2).",
            envvar=["AWS_DEFAULT_REGION", "AWS_REGION"],
        ),
    ] = "eu-west-2",
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output serialization format.",
            case_sensitive=False,
        ),
    ] = OutputFormat.PLAINTEXT,
    sort_by: Annotated[
        SortField,
        typer.Option(
            "--sort-by",
            help="Field used for sorting instances.",
            case_sensitive=False,
        ),
    ] = SortField.EBS_SIZE,
    sort_order: Annotated[
        SortOrder,
        typer.Option(
            "--sort-order",
            help="Sorting direction.",
            case_sensitive=False,
        ),
    ] = SortOrder.ASC,
) -> None:
    """Inspect EC2 instances and summarise attached EBS volume storage."""
    try:
        service = EC2Service(region_name=region)
        instances = service.get_instances(name_filter=name)
        sorted_instances = sort_instances(
            instances, sort_by=sort_by, sort_order=sort_order
        )

        if output_format == OutputFormat.JSON:
            output = format_json(sorted_instances)
        else:
            output = format_plaintext(sorted_instances)

        typer.echo(output)

    except Exception as err:
        typer.echo(f"Error: {err}", err=True)
        raise typer.Exit(code=1) from err


def main() -> None:
    """Entrypoint function for script and wrapper executables."""
    app(prog_name="ec2-ebs-analysis-cli")


if __name__ == "__main__":
    main()
