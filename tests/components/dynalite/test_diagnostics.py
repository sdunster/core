"""Test Dynalite diagnostics."""

from unittest.mock import patch

from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant.typing import ClientSessionGenerator
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

from homeassistant.components import dynalite
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test diagnostics include the config, connection state and entities."""
    entry = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 12345,
            "area": {
                "1": {
                    "name": "Kitchen",
                    "nodefault": True,
                    "channel": {"1": {"name": "Downlight", "type": "light"}},
                },
                "2": {"name": "Fan", "template": "room"},
            },
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert await get_diagnostics_for_config_entry(hass, hass_client, entry) == snapshot(
        exclude=props("context", "last_changed", "last_reported", "last_updated")
    )
