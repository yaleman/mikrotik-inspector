import json

import click

from mikrotik_inspector import connect, parse_response
from mikrotik_inspector.config import Settings, configure_logging


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
def cli(
    command: str,
    host: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> None:
    return main(command, host=host, user=user, debug=debug)


def main(
    command: str,
    host: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> None:
    try:
        logger = configure_logging(debug=debug)

        settings = Settings()  # type: ignore[call-arg]

        username = user or settings.user
        hostname = host or settings.hostname

        if not hostname or hostname is None:
            raise ValueError("Hostname must be provided either via --host or settings.")
        try:
            client = connect(hostname, username)
            result = client.run(command, hide=True)
        except Exception as error:  # noqa: BLE001
            logger.error(f"Failed to connect to {hostname} as {username}: {error}")
            return
        for element in parse_response(result.stdout, logger):
            for key in element:
                if element.get(key) is None:
                    del element[key]

            print(json.dumps(element))
    except BrokenPipeError:
        pass
    finally:
        client.close()


if __name__ == "__main__":
    main()  # ty: ignore[missing-argument]
