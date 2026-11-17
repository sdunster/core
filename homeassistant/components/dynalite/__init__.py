"""Support for the Dynalite networks."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .bridge import DynaliteBridge
from .const import DEFAULT_PORT, DOMAIN, LOGGER, PLATFORMS
from .convert_config import convert_config
from .panel import async_register_dynalite_frontend
from .services import async_setup_services

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DynaliteConfigEntry = ConfigEntry[DynaliteBridge]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Dynalite platform."""
    async_setup_services(hass)

    await async_register_dynalite_frontend(hass)

    return True


async def async_entry_changed(hass: HomeAssistant, entry: DynaliteConfigEntry) -> None:
    """Reload entry since the data has changed."""
    LOGGER.debug("Reconfiguring entry %s", entry.data)
    bridge = entry.runtime_data
    if (entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT)) != (
        bridge.host,
        bridge.port,
    ):
        # The library can't move its connection, so set up the entry again
        hass.config_entries.async_schedule_reload(entry.entry_id)
        return
    bridge.reload_config(entry.data)
    LOGGER.debug("Reconfiguring entry finished %s", entry.data)


async def async_setup_entry(hass: HomeAssistant, entry: DynaliteConfigEntry) -> None:
    """Set up a bridge from a config entry."""
    LOGGER.debug("Setting up entry %s", entry.data)
    bridge = DynaliteBridge(hass, convert_config(entry.data))

    if not await bridge.async_setup():
        raise ConfigEntryNotReady(f"Could not set up bridge at {bridge.host}")

    entry.runtime_data = bridge
    entry.async_on_unload(entry.add_update_listener(async_entry_changed))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass: HomeAssistant, entry: DynaliteConfigEntry) -> None:
    """Unload a config entry."""
    LOGGER.debug("Unloading entry %s", entry.data)
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
    await entry.runtime_data.async_reset()
