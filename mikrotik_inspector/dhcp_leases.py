import click
from fabric import Connection  # type: ignore[import-untyped]

from mikrotik_inspector import connect, parse_dhcp_response
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
def cli(host: str | None = None, user: str | None = None, debug: bool = False) -> None:
    return main(host=host, user=user, debug=debug)


def main(host: str | None = None, user: str | None = None, debug: bool = False) -> None:
    client: Connection | None = None
    try:
        logger = configure_logging(debug=debug)

        settings = Settings()  # type: ignore[call-arg]

        username = user or settings.user
        hostname = host or settings.hostname

        if not hostname or hostname is None:
            logger.error("Hostname must be provided either via --host or settings.")
            return
        try:
            client = connect(hostname, username)
            result = client.run("/ip dhcp-server lease print detail", hide=True)
        except Exception as error:  # noqa: BLE001
            logger.error(f"Failed to connect to {hostname} as {username}: {error}")
            return

        leases = parse_dhcp_response(result.stdout, logger)
        for lease in leases:
            logger.info(lease.model_dump_json(exclude_none=True))
    except BrokenPipeError:
        print("Broken pipe error occurred.")
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
