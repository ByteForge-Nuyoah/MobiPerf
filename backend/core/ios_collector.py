import asyncio
import time
import os
import tempfile
from typing import Dict, Any, Callable, List, Optional
from loguru import logger
from tidevice import Device, Usbmux
from tidevice._perf import Performance, DataType
import subprocess
import re

def _ensure_tidevice_dir():
    tidevice_dir = os.path.expanduser("~/.tidevice")
    ssl_dir = os.path.join(tidevice_dir, "ssl")
    try:
        os.makedirs(ssl_dir, exist_ok=True)
        return True
    except (PermissionError, OSError):
        tidevice_dir = os.path.join(tempfile.gettempdir(), ".tidevice")
        ssl_dir = os.path.join(tidevice_dir, "ssl")
        try:
            os.makedirs(ssl_dir, exist_ok=True)
            os.environ["HOME"] = tempfile.gettempdir()
            return True
        except Exception as e:
            logger.warning(f"Failed to create tidevice directory: {e}")
            return False

class IOSCollector:
    def __init__(self, udid: str):
        _ensure_tidevice_dir()
        self.udid = udid
        self.device = None
        self.perf = None
        self.running = False
        self.target_bundle_id = None
        self._callback: Callable[[Dict[str, Any]], None] = None
        self.device_model = "Unknown iOS Device"
        
        self._current_data = {
            "timestamp": 0,
            "cpu": 0.0,
            "memory": 0.0,
            "fps": 0,
            "jank": 0,
            "gpu": 0.0,
            "battery": {
                "level": 100,
                "temp": 0.0,
                "voltage": 0,
                "current": 0
            },
            "network": {
                "rx": 0,
                "tx": 0
            }
        }
        
        self._last_network_rx = 0
        self._last_network_tx = 0
        self._last_network_time = time.time()
        
        self.screenshot_dir = f"static/screenshots/{self.udid}"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        self._init_device()

    def _init_device(self):
        try:
            _ensure_tidevice_dir()
            self.device = Device(self.udid)
            
            try:
                self.device.mount_developer_image()
                logger.info(f"Developer image mounted for {self.udid}")
            except Exception as e:
                logger.warning(f"Failed to mount developer image: {e}")
            
            device_name = self.device.name or "Unknown"
            product_type = self.device.product_type or ""
            self.device_model = f"{device_name} ({product_type})" if product_type else device_name
            logger.info(f"iOS device initialized: {self.udid} - {self.device_model}")
        except Exception as e:
            logger.error(f"Failed to initialize iOS device {self.udid}: {e}")

    def set_callback(self, callback):
        self._callback = callback

    @staticmethod
    def get_connected_devices() -> List[Dict[str, str]]:
        try:
            devices = []
            mux = Usbmux()
            device_list = mux.device_list()
            
            for device_info in device_list:
                try:
                    udid = device_info.udid
                    d = Device(udid)
                    
                    device_name = d.name or "Unknown iOS Device"
                    product_version = d.product_version or "Unknown"
                    
                    devices.append({
                        "serial": udid,
                        "model": device_name,
                        "platform": "ios",
                        "version": product_version
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for iOS device: {e}")
                    devices.append({
                        "serial": device_info.udid,
                        "model": "Unknown iOS Device",
                        "platform": "ios",
                        "version": "Unknown"
                    })
            return devices
        except Exception as e:
            logger.error(f"Failed to list iOS devices: {e}")
            return []

    @staticmethod
    def get_installed_apps(udid: str) -> List[Dict[str, str]]:
        try:
            result = subprocess.run(
                ['ideviceinstaller', '-u', udid, 'list', '--user'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"ideviceinstaller failed: {result.stderr}")
                return []
            
            apps = []
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split(', ')
                if len(parts) >= 3:
                    bundle_id = parts[0].strip('"')
                    version = parts[1].strip('"') if len(parts) > 1 else ""
                    name = parts[2].strip('"') if len(parts) > 2 else bundle_id.split('.')[-1]
                    apps.append({
                        "package": bundle_id,
                        "name": name,
                        "version": version
                    })
            
            return sorted(apps, key=lambda x: x['name'].lower())
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting iOS apps for {udid}")
            return []
        except Exception as e:
            logger.error(f"Failed to list iOS apps for {udid}: {e}")
            return []

    def set_target(self, bundle_id: str):
        self.target_bundle_id = bundle_id
        logger.info(f"iOS target set to: {bundle_id}")

    async def start(self):
        if not self.target_bundle_id:
            logger.error("iOS collection requires a target bundle ID")
            return False

        if not self.device:
            logger.error("iOS device not initialized")
            return False

        self.running = True
        logger.info(f"Starting iOS collection for {self.udid} on {self.target_bundle_id}")

        try:
            _ensure_tidevice_dir()
            
            self.perf = Performance(
                self.device,
                [DataType.CPU, DataType.MEMORY, DataType.FPS, DataType.GPU]
            )
            
            def _tidevice_callback(datatype, value):
                try:
                    logger.debug(f"iOS {datatype.name}: {value}")
                    if datatype.name == "CPU":
                        self._current_data["cpu"] = value.get("value", 0.0)
                    elif datatype.name == "MEMORY":
                        self._current_data["memory"] = value.get("value", 0.0)
                    elif datatype.name == "FPS":
                        fps_value = value.get("value", 0)
                        self._current_data["fps"] = fps_value
                        self._current_data["jank"] = value.get("jank", 0)
                    elif datatype.name == "GPU":
                        self._current_data["gpu"] = value.get("value", 0.0)
                except Exception as e:
                    logger.error(f"Error in iOS callback: {e}")
            
            self.perf.start(self.target_bundle_id, callback=_tidevice_callback)
            
            asyncio.create_task(self._report_loop())
            asyncio.create_task(self._battery_monitor_loop())
            asyncio.create_task(self._network_monitor_loop())
            asyncio.create_task(self._screenshot_loop())
            
            logger.info(f"iOS collection started successfully for {self.udid}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error starting iOS collection: {e}. Please ensure ~/.tidevice directory is writable.")
            self.running = False
            return False
        except Exception as e:
            logger.error(f"Failed to start iOS collection: {e}")
            self.running = False
            return False

    def stop(self):
        self.running = False
        if self.perf:
            try:
                self.perf.stop()
            except Exception as e:
                logger.error(f"Error stopping iOS perf: {e}")
        
        logger.info(f"Stopped iOS collection for {self.udid}")

    async def _report_loop(self):
        while self.running:
            try:
                timestamp = int(time.time() * 1000)
                self._current_data["timestamp"] = timestamp
                
                if self._callback:
                    report_data = {
                        "type": "monitor",
                        "timestamp": timestamp,
                        "serial": self.udid,
                        "package": self.target_bundle_id,
                        "cpu": self._current_data.get("cpu", 0.0),
                        "memory": self._current_data.get("memory", 0.0),
                        "fps": self._current_data.get("fps", 0),
                        "jank": self._current_data.get("jank", 0),
                        "gpu": self._current_data.get("gpu", 0.0),
                        "battery": self._current_data.get("battery", {}),
                        "network": self._current_data.get("network", {}),
                        "platform": "ios"
                    }
                    self._callback(report_data)
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in iOS report loop: {e}")
                await asyncio.sleep(1)

    async def _battery_monitor_loop(self):
        while self.running:
            try:
                if self.device:
                    try:
                        result = subprocess.run(
                            ['idevicediagnostics', '-u', self.udid, 'ioreg', 'AppleSmartBattery'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            output = result.stdout
                            
                            level_match = re.search(r'"CurrentCapacity"\s*=\s*(\d+)', output)
                            if level_match:
                                self._current_data["battery"]["level"] = int(level_match.group(1))
                            
                            temp_match = re.search(r'"Temperature"\s*=\s*(\d+)', output)
                            if temp_match:
                                temp = int(temp_match.group(1)) / 100.0
                                self._current_data["battery"]["temp"] = temp
                            
                            voltage_match = re.search(r'"Voltage"\s*=\s*(\d+)', output)
                            if voltage_match:
                                self._current_data["battery"]["voltage"] = int(voltage_match.group(1))
                            
                            current_match = re.search(r'"InstantAmperage"\s*=\s*(-?\d+)', output)
                            if current_match:
                                self._current_data["battery"]["current"] = int(current_match.group(1))
                    except subprocess.TimeoutExpired:
                        logger.debug("Battery info timeout")
                    except Exception as e:
                        logger.debug(f"Failed to get battery info: {e}")
                
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in iOS battery monitor: {e}")
                await asyncio.sleep(10)

    async def _network_monitor_loop(self):
        while self.running:
            try:
                if self.device:
                    result = subprocess.run(
                        ['idevicesyslog', '-u', self.udid, '-m', 'network'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    current_time = time.time()
                    time_delta = current_time - self._last_network_time
                    
                    if time_delta > 0:
                        rx_match = re.search(r'rx:\s*(\d+)', result.stdout)
                        tx_match = re.search(r'tx:\s*(\d+)', result.stdout)
                        
                        if rx_match and tx_match:
                            current_rx = int(rx_match.group(1))
                            current_tx = int(tx_match.group(1))
                            
                            rx_speed = (current_rx - self._last_network_rx) / time_delta
                            tx_speed = (current_tx - self._last_network_tx) / time_delta
                            
                            self._current_data["network"]["rx"] = int(rx_speed)
                            self._current_data["network"]["tx"] = int(tx_speed)
                            
                            self._last_network_rx = current_rx
                            self._last_network_tx = current_tx
                            self._last_network_time = current_time
                
                await asyncio.sleep(2)
            except Exception as e:
                logger.debug(f"Network monitoring not available: {e}")
                await asyncio.sleep(5)

    async def _screenshot_loop(self):
        while self.running:
            try:
                timestamp = int(time.time() * 1000)
                screenshot_path = f"{self.screenshot_dir}/{timestamp}.jpg"
                
                result = subprocess.run(
                    ['idevicescreenshot', '-u', self.udid, screenshot_path],
                    capture_output=True,
                    timeout=5
                )
                
                if result.returncode == 0 and os.path.exists(screenshot_path):
                    logger.debug(f"iOS screenshot saved: {screenshot_path}")
                
                await asyncio.sleep(5)
            except subprocess.TimeoutExpired:
                logger.debug("Screenshot timeout")
            except Exception as e:
                logger.debug(f"Screenshot error: {e}")
                await asyncio.sleep(5)

    async def get_device_info(self) -> Dict[str, Any]:
        try:
            if not self.device:
                return {}
            
            info = self.device.device_info
            return {
                "model": info.get("DeviceName", "Unknown"),
                "platform": "ios",
                "version": info.get("ProductVersion", "Unknown"),
                "udid": self.udid,
                "name": info.get("DeviceName", "Unknown"),
                "storage": info.get("TotalDiskCapacity", "Unknown"),
                "battery_level": info.get("BatteryLevel", 100)
            }
        except Exception as e:
            logger.error(f"Failed to get iOS device info: {e}")
            return {}
