import json
from typing import Optional

import click
from mikrotik_inspector.config import Settings, configure_logging
from mikrotik_inspector import connect, parse_response


@click.command()
@click.option(
    "--host", required=False, help="The hostname to connect to, falls back to settings."
)
@click.option(
    "--user",
    required=False,
    help="The username for SSH connection., falls back to settings",
)
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.argument("command")
def main(
    command: str,
    host: Optional[str] = None,
    user: Optional[str] = None,
    debug: bool = False,
) -> None:
    logger = configure_logging(debug=debug)

    settings = Settings()  # type: ignore[call-arg]

    username = user or settings.user
    hostname = host or settings.hostname

    if not hostname or hostname is None:
        raise ValueError("Hostname must be provided either via --host or settings.")

    client = connect(hostname, username)
    result = client.run(command, hide=True)
    for element in parse_response(result.stdout, logger):
        for key in element.keys():
            if element[key] is None:
                del element[key]

        print(json.dumps(element))
    client.close()


if __name__ == "__main__":
    main()
