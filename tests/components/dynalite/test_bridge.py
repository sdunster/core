"""Test Dynalite bridge."""

from unittest.mock import AsyncMock, Mock, patch

from dynalite_devices_lib.dynalite_devices import (
    CONF_AREA as dyn_CONF_AREA,
    CONF_PRESET as dyn_CONF_PRESET,
    NOTIFICATION_PACKET,
    NOTIFICATION_PRESET,
    DynaliteNotification,
)
import pytest
from pytest_homeassistant.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion

from homeassistant.components import dynalite
from homeassistant.components.dynalite.const import (
    ATTR_AREA,
    ATTR_HOST,
    ATTR_PACKET,
    ATTR_PRESET,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect


async def test_update_device(hass: HomeAssistant) -> None:
    """Test that update works."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host})
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        # Not waiting so it add the devices before registration
        update_device_func = mock_dyn_dev.mock_calls[1][2]["update_device_func"]
    device = Mock()
    device.unique_id = "abcdef"
    wide_func = Mock()
    async_dispatcher_connect(hass, f"dynalite-update-{host}", wide_func)
    specific_func = Mock()
    async_dispatcher_connect(
        hass, f"dynalite-update-{host}-{device.unique_id}", specific_func
    )
    update_device_func()
    await hass.async_block_till_done()
    wide_func.assert_called_once()
    specific_func.assert_not_called()
    update_device_func(device)
    await hass.async_block_till_done()
    wide_func.assert_called_once()
    specific_func.assert_called_once()


async def test_add_devices_then_register(hass: HomeAssistant) -> None:
    """Test that add_devices work."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host})
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        # Not waiting so it add the devices before registration
        new_device_func = mock_dyn_dev.mock_calls[1][2]["new_device_func"]
    # Now with devices
    device1 = Mock()
    device1.category = "light"
    device1.name = "NAME"
    device1.unique_id = "unique1"
    device1.brightness = 1
    device2 = Mock()
    device2.category = "switch"
    device2.name = "NAME2"
    device2.unique_id = "unique2"
    device2.brightness = 1
    new_device_func([device1, device2])
    device3 = Mock()
    device3.category = "switch"
    device3.name = "NAME3"
    device3.unique_id = "unique3"
    new_device_func([device3])
    await hass.async_block_till_done()
    assert hass.states.get("light.name")
    assert hass.states.get("switch.name2")
    assert hass.states.get("switch.name3")


async def test_register_then_add_devices(hass: HomeAssistant) -> None:
    """Test that add_devices work after register_add_entities."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host})
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        new_device_func = mock_dyn_dev.mock_calls[1][2]["new_device_func"]
    # Now with devices
    device1 = Mock()
    device1.category = "light"
    device1.name = "NAME"
    device1.unique_id = "unique1"
    device1.brightness = 1
    device2 = Mock()
    device2.category = "switch"
    device2.name = "NAME2"
    device2.unique_id = "unique2"
    device2.brightness = 1
    new_device_func([device1, device2])
    await hass.async_block_till_done()
    assert hass.states.get("light.name")
    assert hass.states.get("switch.name2")


async def test_notifications(hass: HomeAssistant) -> None:
    """Test that update works."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host})
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        notification_func = mock_dyn_dev.mock_calls[1][2]["notification_func"]
    event_listener1 = Mock()
    hass.bus.async_listen("dynalite_packet", event_listener1)
    packet = [5, 4, 3, 2]
    notification_func(
        DynaliteNotification(NOTIFICATION_PACKET, {NOTIFICATION_PACKET: packet})
    )
    await hass.async_block_till_done()
    event_listener1.assert_called_once()
    my_event = event_listener1.mock_calls[0][1][0]
    assert my_event.data[ATTR_HOST] == host
    assert my_event.data[ATTR_PACKET] == packet
    event_listener2 = Mock()
    hass.bus.async_listen("dynalite_preset", event_listener2)
    notification_func(
        DynaliteNotification(
            NOTIFICATION_PRESET, {dyn_CONF_AREA: 7, dyn_CONF_PRESET: 2}
        )
    )
    await hass.async_block_till_done()
    event_listener2.assert_called_once()
    my_event = event_listener2.mock_calls[0][1][0]
    assert my_event.data[ATTR_HOST] == host
    assert my_event.data[ATTR_AREA] == 7
    assert my_event.data[ATTR_PRESET] == 2


ENTRY_DATA = {
    "name": "dynalite",
    "host": "1.2.3.4",
    "port": 12345,
    "autodiscover": False,
    "polltimer": 1.0,
    "active": "on",
    "default": {"fade": 0.5},
    "preset": {
        "1": {"name": "On", "level": 1.0, "fade": 0.5},
        "4": {"name": "Off", "level": 0.0},
    },
    "template": {
        "room": {"room_on": "1", "room_off": "4"},
        "time_cover": {
            "channel_cover": "2",
            "class": "blind",
            "open": "1",
            "close": "2",
            "stop": "3",
            "duration": 30.0,
            "tilt": 2.0,
        },
    },
    "area": {
        "1": {
            "name": "Lights",
            "fade": 1.0,
            "nodefault": True,
            "channel": {
                "1": {"name": "Downlight", "type": "light", "fade": 2.0},
                "2": {"name": "Fan", "type": "switch"},
            },
            "preset": {"5": {"name": "Party", "level": 0.8}},
        },
        "2": {"name": "Room", "template": "room", "room_on": "2", "room_off": "3"},
        "3": {
            "name": "Blind",
            "template": "time_cover",
            "channel_cover": "4",
            "class": "shutter",
            "open": "5",
            "close": "6",
            "stop": "7",
            "duration": 20.0,
            "tilt": 1.5,
        },
    },
}


async def test_entry_data_passed_to_library(
    hass: HomeAssistant, snapshot: SnapshotAssertion
) -> None:
    """Test the config entry data is converted to the library's config format."""
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
            return_value=True,
        ),
        patch(
            "homeassistant.components.dynalite.bridge.DynaliteDevices.configure"
        ) as mock_configure,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    mock_configure.assert_called_once()
    assert mock_configure.call_args.args[0] == snapshot


@pytest.mark.parametrize(
    ("active", "expected"),
    [
        (True, "on"),
        (False, "off"),
        ("on", "on"),
        ("off", "off"),
        ("init", "init"),
    ],
)
async def test_active_passed_to_library(
    hass: HomeAssistant, active: bool | str, expected: str
) -> None:
    """Test each form of the active option maps to the library's value."""
    entry = MockConfigEntry(
        domain=dynalite.DOMAIN, data={CONF_HOST: "1.2.3.4", "active": active}
    )
    entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
            return_value=True,
        ),
        patch(
            "homeassistant.components.dynalite.bridge.DynaliteDevices.configure"
        ) as mock_configure,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert mock_configure.call_args.args[0]["active"] == expected
