"""The qy_water integration."""
from __future__ import annotations

from datetime import timedelta
import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_OID,
    CONF_UPDATE_TIME,
    DOMAIN,
    LOGGER,
    USER_AGENT,
    BASE_URL,
    DEFAULT_UPDATE_INTERVAL
)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up qy_water from a config entry."""
    try:
        await hass.async_add_executor_job(_ensure_dependencies)
    except ImportError as err:
        LOGGER.error("依赖加载失败: %s", err)
        return False

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_OID])},
        manufacturer="清远市供水拓展有限责任公司",
        name=f"水表 {entry.data[CONF_OID]}",
        model="清远水务"
    )

    coordinator = QYWaterDataUpdateCoordinator(
        hass,
        entry=entry,
        update_interval=timedelta(
            minutes=entry.data.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_INTERVAL)
        )
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "oid": entry.data[CONF_OID]
    }

    # 异步加载平台以避免阻塞事件循环
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

def _ensure_dependencies():
    """确保依赖包已加载"""
    import requests  # noqa: F401
    from bs4 import BeautifulSoup  # noqa: F401

class QYWaterDataUpdateCoordinator(DataUpdateCoordinator):
    """自定义数据更新协调器"""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_OID]}",
            update_interval=update_interval,
        )
        self.entry = entry

    async def _async_update_data(self):
        """从API获取数据"""
        try:
            data = await self.hass.async_add_executor_job(
                self._fetch_water_data
            )
            if not data:
                raise UpdateFailed("获取到空数据")
            return data
        except Exception as err:
            raise UpdateFailed(f"更新水费数据失败: {err}") from err

    def _fetch_water_data(self):
        """精确提取网页数据"""
        import requests
        from bs4 import BeautifulSoup

        oid = self.entry.data[CONF_OID]
        url = f"{BASE_URL}&oid={oid}"
        
        try:
            LOGGER.debug("正在请求URL: %s", url)
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=20
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            LOGGER.debug("网页内容片段: %s", response.text[:500])

            # 1. 提取上月月份 (从第一个表格行的第二列)
            last_month_day = None
            first_row = soup.select_one("tr[onMouseOver]")
            if first_row:
                month_cell = first_row.select("td:nth-of-type(2)")
                if month_cell:
                    last_month_day = month_cell[0].get_text(strip=True)

            # 2. 提取上月用水量 (从第一个表格行的第三列)
            last_month_usage = None
            if first_row:
                usage_cell = first_row.select("td:nth-of-type(3)")
                if usage_cell:
                    try:
                        last_month_usage = float(usage_cell[0].get_text(strip=True))
                    except (ValueError, TypeError):
                        last_month_usage = 0
                        LOGGER.warning("用水量数据格式错误")

            # 3. 提取上月金额 (从第一个表格行的第四列)
            last_month_cost = None
            if first_row:
                cost_cell = first_row.select("td:nth-of-type(4)")
                if cost_cell:
                    try:
                        last_month_cost = float(cost_cell[0].get_text(strip=True))
                    except (ValueError, TypeError):
                        last_month_cost = 0
                        LOGGER.warning("金额数据格式错误")

            # 4. 提取总欠费 (从包含"欠费总额"的单元格)
            arrears = 0
            arrears_cells = soup.find_all("td", string=lambda t: t and "欠费总额" in t)
            if arrears_cells:
                arrears_text = arrears_cells[0].get_text(strip=True)
                match = re.search(r"欠费总额：([\d.-]+)", arrears_text)
                if match:
                    try:
                        arrears = float(match.group(1))
                    except (ValueError, TypeError):
                        arrears = 0
                        LOGGER.warning("欠费总额数据格式错误")
                else:
                    LOGGER.debug("未找到欠费总额数值")

            # 5. 提取余额 (从水表选择框的option文本中)
            balance = 0
            meter_select = soup.find("select", id="BindingMeter")
            if meter_select:
                selected_option = meter_select.find("option", selected=True)
                if selected_option:
                    option_text = selected_option.get_text(strip=True)
                    match = re.search(r"【余额([\d.-]+)】", option_text)
                    if match:
                        try:
                            balance = float(match.group(1))
                        except (ValueError, TypeError):
                            balance = 0
                            LOGGER.warning("余额数据格式错误")
                    else:
                        LOGGER.debug("未找到余额数值")

            data = {
                "water_last_month_day": last_month_day or "未知",
                "water_last_month_total_usage": last_month_usage or 0,
                "water_last_month_total_cost": last_month_cost or 0,
                "water_arrears": arrears,
                "water_balance": balance  # 新增余额字段
            }

            LOGGER.debug("解析结果: %s", data)
            return data
            
        except requests.RequestException as err:
            LOGGER.error("请求失败: %s", str(err))
            raise
        except Exception as err:
            LOGGER.error("解析失败: %s", str(err), exc_info=True)
            raise