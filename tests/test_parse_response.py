import logging
from datetime import timedelta

import pytest

from mikrotik_inspector import parse_dhcp_response, LeaseInfo, parse_duration


EXAMPLE = """Flags: X - disabled, R - radius, D - dynamic, B - blocked
65 D address=10.0.5.146 mac-address=BC:DD:C2:29:73:B7 address-lists=""
     server=guest dhcp-option="" status=bound expires-after=4h29m
     last-seen=3h31m active-address=10.0.5.146
     active-mac-address=BC:DD:C2:29:73:B7 active-server=guest
     host-name="tasmota-2973B7-5047"
"""


def test_parse_response() -> None:
    leases = parse_dhcp_response(EXAMPLE, logging.getLogger("test_parse_response"))

    assert isinstance(leases, list)
    assert all(isinstance(lease, LeaseInfo) for lease in leases)
    assert len(leases) == 1


def test_parse_duration() -> None:
    assert parse_duration("4h29m") == timedelta(hours=4, minutes=29)
    assert parse_duration("3w2d3h15m10s") == timedelta(
        weeks=3, days=2, hours=3, minutes=15, seconds=10
    )
    assert parse_duration("2d3h15m10s") == timedelta(
        days=2, hours=3, minutes=15, seconds=10
    )
    assert parse_duration("10m") == timedelta(minutes=10)
    assert parse_duration("5s") == timedelta(seconds=5)
    assert parse_duration("1d") == timedelta(days=1)
    with pytest.raises(ValueError):
        assert parse_duration("invalid") is None
    assert parse_duration("") is None
    assert parse_duration("never") is None
