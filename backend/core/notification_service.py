import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from loguru import logger
import asyncio


class NotificationType(str, Enum):
    PERFORMANCE_ALERT = "performance_alert"
    DEVICE_STATUS = "device_status"
    TEST_COMPLETE = "test_complete"
    REPORT_GENERATED = "report_generated"
    SYSTEM_MESSAGE = "system_message"
    COLLABORATION = "collaboration"
    THRESHOLD_BREACH = "threshold_breach"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    BROWSER = "browser"
    WEBSOCKET = "websocket"


class Notification:
    def __init__(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ):
        self.id = str(id(self))
        self.type = notification_type
        self.title = title
        self.message = message
        self.priority = priority
        self.data = data or {}
        self.channels = channels or [NotificationChannel.IN_APP, NotificationChannel.WEBSOCKET]
        self.created_at = datetime.now()
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "data": self.data,
            "channels": [ch.value for ch in self.channels],
            "created_at": self.created_at.isoformat(),
            "read": self.read
        }


class NotificationConfig:
    def __init__(self):
        self.enabled_types: Dict[str, bool] = {
            NotificationType.PERFORMANCE_ALERT.value: True,
            NotificationType.DEVICE_STATUS.value: True,
            NotificationType.TEST_COMPLETE.value: True,
            NotificationType.REPORT_GENERATED.value: True,
            NotificationType.SYSTEM_MESSAGE.value: True,
            NotificationType.COLLABORATION.value: True,
            NotificationType.THRESHOLD_BREACH.value: True
        }
        
        self.enabled_channels: Dict[str, bool] = {
            NotificationChannel.IN_APP.value: True,
            NotificationChannel.EMAIL.value: False,
            NotificationChannel.BROWSER.value: False,
            NotificationChannel.WEBSOCKET.value: True
        }
        
        self.thresholds = {
            "fps_low": 30,
            "fps_critical": 20,
            "cpu_high": 80,
            "cpu_critical": 95,
            "memory_high": 500,
            "memory_critical": 800,
            "battery_low": 20,
            "battery_critical": 10,
            "temperature_high": 45,
            "temperature_critical": 50
        }
        
        self.quiet_hours = {
            "enabled": False,
            "start": "22:00",
            "end": "08:00"
        }
    
    def is_type_enabled(self, notification_type: NotificationType) -> bool:
        return self.enabled_types.get(notification_type.value, False)
    
    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        return self.enabled_channels.get(channel.value, False)
    
    def is_quiet_hours(self) -> bool:
        if not self.quiet_hours["enabled"]:
            return False
        
        now = datetime.now()
        start_hour, start_min = map(int, self.quiet_hours["start"].split(":"))
        end_hour, end_min = map(int, self.quiet_hours["end"].split(":"))
        
        current_minutes = now.hour * 60 + now.minute
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        if start_minutes < end_minutes:
            return start_minutes <= current_minutes < end_minutes
        else:
            return current_minutes >= start_minutes or current_minutes < end_minutes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled_types": self.enabled_types,
            "enabled_channels": self.enabled_channels,
            "thresholds": self.thresholds,
            "quiet_hours": self.quiet_hours
        }
    
    def update_from_dict(self, config: Dict[str, Any]):
        if "enabled_types" in config:
            self.enabled_types.update(config["enabled_types"])
        if "enabled_channels" in config:
            self.enabled_channels.update(config["enabled_channels"])
        if "thresholds" in config:
            self.thresholds.update(config["thresholds"])
        if "quiet_hours" in config:
            self.quiet_hours.update(config["quiet_hours"])


class NotificationService:
    def __init__(self):
        self.notifications: List[Notification] = []
        self.config = NotificationConfig()
        self.websocket_callbacks: List[callable] = []
        self.max_notifications = 100
    
    def register_websocket_callback(self, callback: callable):
        self.websocket_callbacks.append(callback)
    
    def unregister_websocket_callback(self, callback: callable):
        if callback in self.websocket_callbacks:
            self.websocket_callbacks.remove(callback)
    
    async def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Optional[Notification]:
        if not self.config.is_type_enabled(notification_type):
            logger.debug(f"Notification type {notification_type} is disabled")
            return None
        
        if self.config.is_quiet_hours() and priority != NotificationPriority.CRITICAL:
            logger.debug("Quiet hours enabled, skipping notification")
            return None
        
        notification = Notification(
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data,
            channels=channels
        )
        
        self.notifications.insert(0, notification)
        
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[:self.max_notifications]
        
        await self._broadcast_notification(notification)
        
        logger.info(f"Created notification: {notification_type.value} - {title}")
        return notification
    
    async def _broadcast_notification(self, notification: Notification):
        for callback in self.websocket_callbacks:
            try:
                await callback(notification.to_dict())
            except Exception as e:
                logger.error(f"Error broadcasting notification: {e}")
    
    async def check_performance_thresholds(self, metrics: Dict[str, Any], device_serial: str):
        thresholds = self.config.thresholds
        
        if metrics.get("fps"):
            fps = metrics["fps"]
            if fps < thresholds["fps_critical"]:
                await self.create_notification(
                    NotificationType.THRESHOLD_BREACH,
                    "FPS 严重过低",
                    f"设备 {device_serial} FPS 降至 {fps}，严重影响用户体验",
                    NotificationPriority.CRITICAL,
                    {"device_serial": device_serial, "fps": fps, "threshold": thresholds["fps_critical"]}
                )
            elif fps < thresholds["fps_low"]:
                await self.create_notification(
                    NotificationType.PERFORMANCE_ALERT,
                    "FPS 过低警告",
                    f"设备 {device_serial} FPS 为 {fps}，低于正常水平",
                    NotificationPriority.HIGH,
                    {"device_serial": device_serial, "fps": fps, "threshold": thresholds["fps_low"]}
                )
        
        if metrics.get("cpu"):
            cpu = metrics["cpu"]
            if cpu > thresholds["cpu_critical"]:
                await self.create_notification(
                    NotificationType.THRESHOLD_BREACH,
                    "CPU 使用率严重过高",
                    f"设备 {device_serial} CPU 使用率达到 {cpu}%",
                    NotificationPriority.CRITICAL,
                    {"device_serial": device_serial, "cpu": cpu, "threshold": thresholds["cpu_critical"]}
                )
            elif cpu > thresholds["cpu_high"]:
                await self.create_notification(
                    NotificationType.PERFORMANCE_ALERT,
                    "CPU 使用率过高警告",
                    f"设备 {device_serial} CPU 使用率为 {cpu}%",
                    NotificationPriority.HIGH,
                    {"device_serial": device_serial, "cpu": cpu, "threshold": thresholds["cpu_high"]}
                )
        
        if metrics.get("memory"):
            memory = metrics["memory"]
            if memory > thresholds["memory_critical"]:
                await self.create_notification(
                    NotificationType.THRESHOLD_BREACH,
                    "内存使用严重过高",
                    f"设备 {device_serial} 内存使用达到 {memory}MB",
                    NotificationPriority.CRITICAL,
                    {"device_serial": device_serial, "memory": memory, "threshold": thresholds["memory_critical"]}
                )
            elif memory > thresholds["memory_high"]:
                await self.create_notification(
                    NotificationType.PERFORMANCE_ALERT,
                    "内存使用过高警告",
                    f"设备 {device_serial} 内存使用为 {memory}MB",
                    NotificationPriority.HIGH,
                    {"device_serial": device_serial, "memory": memory, "threshold": thresholds["memory_high"]}
                )
        
        if metrics.get("battery", {}).get("level"):
            battery = metrics["battery"]["level"]
            if battery < thresholds["battery_critical"]:
                await self.create_notification(
                    NotificationType.DEVICE_STATUS,
                    "电池电量严重不足",
                    f"设备 {device_serial} 电量仅剩 {battery}%",
                    NotificationPriority.CRITICAL,
                    {"device_serial": device_serial, "battery": battery}
                )
            elif battery < thresholds["battery_low"]:
                await self.create_notification(
                    NotificationType.DEVICE_STATUS,
                    "电池电量不足",
                    f"设备 {device_serial} 电量为 {battery}%",
                    NotificationPriority.MEDIUM,
                    {"device_serial": device_serial, "battery": battery}
                )
        
        if metrics.get("battery", {}).get("temp"):
            temp = metrics["battery"]["temp"]
            if temp > thresholds["temperature_critical"]:
                await self.create_notification(
                    NotificationType.THRESHOLD_BREACH,
                    "设备温度严重过高",
                    f"设备 {device_serial} 温度达到 {temp}°C",
                    NotificationPriority.CRITICAL,
                    {"device_serial": device_serial, "temperature": temp}
                )
            elif temp > thresholds["temperature_high"]:
                await self.create_notification(
                    NotificationType.PERFORMANCE_ALERT,
                    "设备温度过高警告",
                    f"设备 {device_serial} 温度为 {temp}°C",
                    NotificationPriority.HIGH,
                    {"device_serial": device_serial, "temperature": temp}
                )
    
    def get_notifications(
        self,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        notifications = self.notifications
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        
        return [n.to_dict() for n in notifications[:limit]]
    
    def mark_as_read(self, notification_id: str) -> bool:
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    def mark_all_as_read(self) -> int:
        count = 0
        for notification in self.notifications:
            if not notification.read:
                notification.read = True
                count += 1
        return count
    
    def delete_notification(self, notification_id: str) -> bool:
        for i, notification in enumerate(self.notifications):
            if notification.id == notification_id:
                self.notifications.pop(i)
                return True
        return False
    
    def clear_all_notifications(self):
        self.notifications.clear()
    
    def get_unread_count(self) -> int:
        return sum(1 for n in self.notifications if not n.read)
    
    def update_config(self, config: Dict[str, Any]):
        self.config.update_from_dict(config)
        logger.info("Notification config updated")
    
    def get_config(self) -> Dict[str, Any]:
        return self.config.to_dict()


notification_service = NotificationService()
