"""Config flow to configure Dynalite hub."""

import asyncio
from typing import Any, override

import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_PORT, DOMAIN, LOGGER

CONNECT_TIMEOUT = 10


class DynaliteFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Dynalite config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Dynalite flow."""
        self.host = None

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step when user initializes a integration."""
        if user_input is not None:
            return await self._try_create(user_input)

        schema = probatio.Schema(
            {
                probatio.Required(CONF_HOST): cv.string,
                probatio.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def _try_create(self, info: dict[str, Any]) -> ConfigFlowResult:
        """Try to connect and if successful, create entry."""
        host = info[CONF_HOST]
        configured_hosts = [
            entry.data[CONF_HOST] for entry in self._async_current_entries()
        ]
        if host in configured_hosts:
            return self.async_abort(reason="already_configured")
        if not await _async_can_connect(host, info.get(CONF_PORT, DEFAULT_PORT)):
            LOGGER.error("Unable to connect to the gateway - info=%s", info)
            return self.async_abort(reason="cannot_connect")
        LOGGER.debug("Creating entry for the bridge - %s", info)
        return self.async_create_entry(title=info[CONF_HOST], data=info)


async def _async_can_connect(host: str, port: int) -> bool:
    """Check that the gateway accepts a TCP connection, then close it."""
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            _, writer = await asyncio.open_connection(host, port)
    except OSError, TimeoutError:
        LOGGER.debug("Unable to connect to %s:%s", host, port)
        return False
    writer.close()
    await writer.wait_closed()
    return True
