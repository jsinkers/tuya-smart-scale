"""The Tuya Smart Scale integration."""
import logging
from datetime import datetime, date

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import (
    DOMAIN, 
    CONF_ACCESS_ID,
    CONF_ACCESS_KEY,
    CONF_DEVICE_ID, 
    CONF_REGION,
    CONF_BIRTHDATE,
    CONF_SEX,
    DEFAULT_SEX,
    DEFAULT_BIRTHDATE
)
from .api import TuyaSmartScaleAPI
from .coordinator import TuyaSmartScaleDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

def calculate_age_from_birthdate(birthdate_str: str) -> int:
    """Calculate current age from birthdate string."""
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    except (ValueError, TypeError):
        _LOGGER.warning(f"Invalid birthdate format: {birthdate_str}, using default age 30")
        return 30

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tuya Smart Scale from a config entry."""
    
    api_client = TuyaSmartScaleAPI(
        access_id=entry.data[CONF_ACCESS_ID],
        access_key=entry.data[CONF_ACCESS_KEY],
        device_id=entry.data[CONF_DEVICE_ID],
        region=entry.data.get(CONF_REGION, "eu"),
        birthdate=entry.data.get(CONF_BIRTHDATE, DEFAULT_BIRTHDATE),
        sex=entry.data.get(CONF_SEX, DEFAULT_SEX)
    )
    
    coordinator = TuyaSmartScaleDataCoordinator(hass, api_client)
    
    # Do initial data update
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator for this entry
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok