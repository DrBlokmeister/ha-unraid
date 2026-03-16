"""
The Unraid integration.

This integration connects Home Assistant to Unraid servers via the unraid-api library.
Provides monitoring and control for system metrics, storage, Docker, and VMs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    Platform,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from unraid_api import ServerInfo, UnraidClient
from unraid_api.exceptions import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidSSLError,
    UnraidTimeoutError,
)

from .const import (
    CONF_IGNORE_SSL,
    DEFAULT_PORT,
    DOMAIN,
    REPAIR_AUTH_FAILED,
)
from .coordinator import (
    UnraidInfraCoordinator,
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]


@dataclass
class UnraidRuntimeData:
    """Runtime data for Unraid integration (stored in entry.runtime_data)."""

    api_client: UnraidClient
    system_coordinator: UnraidSystemCoordinator
    storage_coordinator: UnraidStorageCoordinator
    infra_coordinator: UnraidInfraCoordinator
    server_info: dict


# Type alias for config entries with runtime data
type UnraidConfigEntry = ConfigEntry[UnraidRuntimeData]


def _build_server_info(server_info: ServerInfo, host: str, use_ssl: bool) -> dict:
    """Build server info dictionary from library's ServerInfo model."""
    # Use library's ServerInfo model directly
    # Model shows "Unraid {version}" for prominent display in Device Info
    unraid_version = server_info.sw_version or "Unknown"
    model = f"Unraid {unraid_version}"

    server_name = server_info.hostname or host

    # Determine configuration URL for device info
    configuration_url = server_info.local_url
    if not configuration_url and server_info.lan_ip:
        protocol = "https" if use_ssl else "http"
        configuration_url = f"{protocol}://{server_info.lan_ip}"

    return {
        "uuid": server_info.uuid,
        "name": server_name,
        "manufacturer": server_info.manufacturer,
        "model": model,
        "serial_number": server_info.serial_number,
        "sw_version": unraid_version,
        "hw_version": server_info.hw_version,
        "os_distro": server_info.os_distro,
        "os_release": server_info.os_release,
        "os_arch": server_info.os_arch,
        "api_version": server_info.api_version,
        "license_type": server_info.license_type,
        "lan_ip": server_info.lan_ip,
        "configuration_url": configuration_url,
        "cpu_brand": server_info.cpu_brand,
        "cpu_cores": server_info.cpu_cores,
        "cpu_threads": server_info.cpu_threads,
        # Hardware info for diagnostics
        "hw_manufacturer": server_info.hw_manufacturer,
        "hw_model": server_info.hw_model,
    }


async def _connect_client(
    hass: HomeAssistant,
    host: str,
    port: int,
    api_key: str,
    ignore_ssl: bool,
) -> tuple[UnraidClient, ServerInfo]:
    """Connect a client and fetch server info."""
    session = async_get_clientsession(hass, verify_ssl=not ignore_ssl)
    api_client = UnraidClient(
        host=host,
        http_port=port,
        api_key=api_key,
        verify_ssl=not ignore_ssl,
        session=session,
    )
    await api_client.test_connection()
    info = await api_client.get_server_info()
    return api_client, info


async def _connect_with_tls_fallback(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    host: str,
    port: int,
    api_key: str,
    ignore_ssl: bool,
) -> tuple[UnraidClient, ServerInfo, bool]:
    """Connect to Unraid and optionally retry with TLS verification disabled."""
    try:
        api_client, info = await _connect_client(
            hass,
            host,
            port,
            api_key,
            ignore_ssl=ignore_ssl,
        )
        ir.async_delete_issue(hass, DOMAIN, REPAIR_AUTH_FAILED)
        _LOGGER.debug("Initial API connectivity check succeeded for %s", host)
        return api_client, info, ignore_ssl
    except UnraidAuthenticationError as err:
        ir.async_create_issue(
            hass,
            DOMAIN,
            REPAIR_AUTH_FAILED,
            is_fixable=True,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="auth_failed",
            translation_placeholders={"host": host},
        )
        msg = f"Authentication failed for Unraid server {host}"
        raise ConfigEntryAuthFailed(msg) from err
    except UnraidSSLError as err:
        error_text = str(err)
        error_lower = error_text.lower()
        _LOGGER.warning(
            "TLS verification failed for %s (ignore_ssl=%s): %s",
            host,
            ignore_ssl,
            err,
        )
        _LOGGER.debug(
            "TLS failure details for %s: error_type=%s cause_type=%s repr=%r",
            host,
            type(err).__name__,
            type(err.__cause__).__name__ if err.__cause__ else "None",
            err,
        )
        if "hostname" in error_lower or "ip address mismatch" in error_lower:
            _LOGGER.info(
                "Certificate hostname validation failed for %s. "
                "Use the certificate hostname in host field or enable ignore_ssl.",
                host,
            )
        elif "self-signed" in error_lower:
            _LOGGER.info(
                "Self-signed certificate detected for %s. "
                "Enable ignore_ssl to accept it.",
                host,
            )

        if ignore_ssl:
            msg = f"SSL certificate error connecting to Unraid server {host}: {err}"
            raise ConfigEntryNotReady(msg) from err

        _LOGGER.info(
            "Retrying setup for %s with TLS verification disabled. "
            "This often happens with self-signed certificates or host/IP mismatch "
            "(cert CN/SAN may be hostname while HA uses IP).",
            host,
        )

        try:
            api_client, info = await _connect_client(
                hass,
                host,
                port,
                api_key,
                ignore_ssl=True,
            )
            ir.async_delete_issue(hass, DOMAIN, REPAIR_AUTH_FAILED)
            _LOGGER.warning(
                "Connected to %s with TLS verification disabled; persisting "
                "ignore_ssl=True in config entry",
                host,
            )
            hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_SSL: True,
                    CONF_IGNORE_SSL: True,
                },
            )
            return api_client, info, True
        except UnraidAuthenticationError as fallback_err:
            ir.async_create_issue(
                hass,
                DOMAIN,
                REPAIR_AUTH_FAILED,
                is_fixable=True,
                is_persistent=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_failed",
                translation_placeholders={"host": host},
            )
            msg = f"Authentication failed for Unraid server {host}"
            raise ConfigEntryAuthFailed(msg) from fallback_err
        except UnraidSSLError as fallback_err:
            msg = (
                f"SSL certificate error connecting to Unraid server {host}: "
                f"{fallback_err}"
            )
            raise ConfigEntryNotReady(msg) from fallback_err
        except (UnraidConnectionError, UnraidTimeoutError) as fallback_err:
            _LOGGER.warning(
                "Connection to %s failed during TLS fallback: %s",
                host,
                fallback_err,
            )
            msg = f"Failed to connect to Unraid server: {fallback_err}"
            raise ConfigEntryNotReady(msg) from fallback_err
        except UnraidAPIError as fallback_err:
            msg = f"Unraid API error connecting to server {host}: {fallback_err}"
            raise ConfigEntryNotReady(msg) from fallback_err
    except (UnraidConnectionError, UnraidTimeoutError) as err:
        _LOGGER.warning("Connection to %s failed: %s", host, err)
        msg = f"Failed to connect to Unraid server: {err}"
        raise ConfigEntryNotReady(msg) from err
    except UnraidAPIError as err:
        msg = f"Unraid API error connecting to server {host}: {err}"
        raise ConfigEntryNotReady(msg) from err


async def async_setup_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Set up Unraid from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    api_key = entry.data[CONF_API_KEY]
    use_ssl = entry.data.get(CONF_SSL, True)
    ignore_ssl = entry.data.get(CONF_IGNORE_SSL, False)

    _LOGGER.debug(
        "Starting setup for %s with http_port=%s ssl=%s ignore_ssl=%s",
        host,
        port,
        use_ssl,
        ignore_ssl,
    )

    api_client, info, ignore_ssl = await _connect_with_tls_fallback(
        hass=hass,
        entry=entry,
        host=host,
        port=port,
        api_key=api_key,
        ignore_ssl=ignore_ssl,
    )

    # Build server info using helper function
    server_info = _build_server_info(info, host, use_ssl)
    server_name = server_info["name"]

    # Create coordinators (use fixed internal intervals per HA Core requirements)
    system_coordinator = UnraidSystemCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        config_entry=entry,
    )

    storage_coordinator = UnraidStorageCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        config_entry=entry,
    )

    infra_coordinator = UnraidInfraCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        config_entry=entry,
    )

    # Fetch initial data
    try:
        await system_coordinator.async_config_entry_first_refresh()
        await storage_coordinator.async_config_entry_first_refresh()
        await infra_coordinator.async_config_entry_first_refresh()
    except (ConfigEntryAuthFailed, ConfigEntryNotReady):
        await api_client.close()
        raise

    # Store runtime data in config entry (HA 2024.4+ pattern)
    entry.runtime_data = UnraidRuntimeData(
        api_client=api_client,
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        infra_coordinator=infra_coordinator,
        server_info=server_info,
    )

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Unraid integration setup complete for %s",
        server_name,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close API client
        await entry.runtime_data.api_client.close()
        _LOGGER.info("Unraid integration unloaded for entry %s", entry.title)

    return unload_ok
