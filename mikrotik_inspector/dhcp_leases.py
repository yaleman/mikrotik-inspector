from typing import Optional

import click
from mikrotik_inspector.config import Settings, configure_logging
from mikrotik_inspector import connect, parse_dhcp_response


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
def main(
    host: Optional[str] = None, user: Optional[str] = None, debug: bool = False
) -> None:
    logger = configure_logging(debug=debug)

    settings = Settings()  # type: ignore[call-arg]

    username = user or settings.user
    hostname = host or settings.hostname

    if not hostname or hostname is None:
        raise ValueError("Hostname must be provided either via --host or settings.")

    client = connect(hostname, username)
    result = client.run("/ip dhcp-server lease print detail", hide=True)

    leases = parse_dhcp_response(result.stdout, logger)

    for lease in leases:
        logger.info(lease.model_dump_json(exclude_none=True))
    client.close()


if __name__ == "__main__":
    main()
