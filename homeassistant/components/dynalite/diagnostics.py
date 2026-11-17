"""Diagnostics support for Philips Dynalite."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .bridge import DynaliteConfigEntry

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: DynaliteConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entity_registry = er.async_get(hass)
    entities = []
    for entity_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        state = hass.states.get(entity_entry.entity_id)
        entities.append(
            {
                "entity_id": entity_entry.entity_id,
                "unique_id": entity_entry.unique_id,
                "disabled_by": entity_entry.disabled_by,
                "state": state.as_dict() if state else None,
            }
        )
    return {
        "config": async_redact_data(dict(entry.data), TO_REDACT),
        "connected": entry.runtime_data.dynalite_devices.connected,
        "entities": entities,
    }
