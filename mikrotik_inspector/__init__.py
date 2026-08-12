import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Self

from fabric import Connection  # type: ignore[import-untyped]
from pydantic import BaseModel, Configdict, Field, model_validator

START_NEW = re.compile(r"^\s*\d+")


def connect(hostname: str, username: str | None) -> Connection:
    """Establish an SSH connection to the specified hostname."""
    return Connection(host=hostname, user=username)


class LeaseInfo(BaseModel):
    record_id: str = Field(alias="id")
    server: str
    active_server: str | None = Field(None, alias="active-server")

    host_name: str | None = Field(None, alias="host-name")

    mac_address: str = Field(alias="mac-address")
    active_mac_address: str | None = Field(None, alias="active-mac-address")

    address: str | None = None
    active_address: str | None = Field(None, alias="active-address")

    status: str | None = None

    client_id: str | None = Field(None, alias="client-id")
    active_client_id: str | None = Field(None, alias="active-client-id")

    class_id: str | None = Field(None, alias="class-id")
    age: str | None = None

    last_seen: str | datetime | None = Field(None, alias="last-seen")
    expires_after: str | datetime | None = Field(None, alias="expires-after")

    model_config = Configdict(extra="forbid")

    @model_validator(mode="after")
    def convert_durations(self) -> Self:
        """Convert duration strings to timedelta objects after model initialization."""
        now = datetime.now(UTC)
        if self.last_seen is not None and isinstance(self.last_seen, str):
            parsed_duration = parse_duration(self.last_seen)
            if parsed_duration is not None:
                self.last_seen = now - parsed_duration

        if self.expires_after is not None and isinstance(self.expires_after, str):
            parsed_duration = parse_duration(self.expires_after)
            if parsed_duration is not None:
                self.expires_after = parsed_duration + now

        return self


def parse_kv(entry: str) -> tuple[str, str] | None:
    """Parse a key=value pair and return the key and value."""
    if "=" not in entry:
        return None
    key, value = entry.split("=", 1)
    return key.strip(), value.strip().strip('"')


DURATION_PARSER = re.compile(r"(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(duration_str: str) -> timedelta | None:
    """Parse a duration string like '4h29m' into a timedelta object."""
    if (
        duration_str is None
        or duration_str.strip() == ""
        or duration_str.strip().lower() == "never"
    ):
        return None
    match = DURATION_PARSER.fullmatch(duration_str.strip())
    if not match:
        raise ValueError(f"Invalid duration string: {duration_str}")

    weeks, days, hours, minutes, seconds = match.groups(default="0")
    return timedelta(
        weeks=int(weeks),
        days=int(days),
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds),
    )


def parse_response(response: str, logger: logging.Logger) -> list[dict[str, str]]:
    current_record: dict[str, str] = {}
    records: list[dict[str, str]] = []
    for line in response.strip().splitlines():
        if line.startswith("Flags:"):
            continue  # skip header line
        logger.debug(f"{line=}")
        parts = line.split()
        if START_NEW.match(line):
            # new record
            if current_record:
                logger.debug(f"adding new record: {current_record=}")
                records.append(current_record)
            current_record = {"id": parts.pop(0)}
        for part in parts:
            kv = parse_kv(part)
            if kv:
                key, value = kv
                if value.strip() != "":
                    current_record[key] = value
    if current_record:
        records.append(current_record)
    return records


def parse_dhcp_response(response: str, logger: logging.Logger) -> list[LeaseInfo]:
    """Parse and display the DHCP lease information from the response."""

    leases: list[LeaseInfo] = []
    lines = response.strip().splitlines()

    current_record: dict[str, str] = {}
    for line in lines:
        if line.startswith("Flags:"):
            continue  # skip header line
        logger.debug(f"{line=}")
        parts = line.split()
        if START_NEW.match(line):
            # new record
            if current_record:
                logger.debug(f"adding new record: {current_record=}")
                leases.append(LeaseInfo(**current_record))
            current_record = {"id": parts.pop(0)}
        for part in parts:
            kv = parse_kv(part)
            if kv:
                key, value = kv
                if value.strip() != "":
                    current_record[key] = value

    if current_record:
        leases.append(LeaseInfo(**current_record))
    return leases
