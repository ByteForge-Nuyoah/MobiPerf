from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from core.notification_service import (
    notification_service,
    NotificationType,
    NotificationPriority
)
from loguru import logger

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationConfigUpdate(BaseModel):
    enabled_types: Optional[Dict[str, bool]] = None
    enabled_channels: Optional[Dict[str, bool]] = None
    thresholds: Optional[Dict[str, int]] = None
    quiet_hours: Optional[Dict[str, Any]] = None


class CreateNotificationRequest(BaseModel):
    type: str
    title: str
    message: str
    priority: Optional[str] = "medium"
    data: Optional[Dict[str, Any]] = None


@router.get("/")
async def get_notifications(
    unread_only: bool = Query(False, description="仅获取未读通知"),
    notification_type: Optional[str] = Query(None, description="通知类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制")
):
    """获取通知列表"""
    try:
        notif_type = None
        if notification_type:
            try:
                notif_type = NotificationType(notification_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid notification type")
        
        notifications = notification_service.get_notifications(
            unread_only=unread_only,
            notification_type=notif_type,
            limit=limit
        )
        
        return {
            "notifications": notifications,
            "total": len(notifications),
            "unread_count": notification_service.get_unread_count()
        }
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count():
    """获取未读通知数量"""
    return {"count": notification_service.get_unread_count()}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """标记通知为已读"""
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_as_read():
    """标记所有通知为已读"""
    count = notification_service.mark_all_as_read()
    return {"success": True, "marked_count": count}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """删除通知"""
    success = notification_service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "message": "Notification deleted"}


@router.delete("/")
async def clear_all_notifications():
    """清空所有通知"""
    notification_service.clear_all_notifications()
    return {"success": True, "message": "All notifications cleared"}


@router.get("/config")
async def get_notification_config():
    """获取通知配置"""
    return notification_service.get_config()


@router.put("/config")
async def update_notification_config(config: NotificationConfigUpdate):
    """更新通知配置"""
    try:
        config_dict = config.dict(exclude_unset=True)
        notification_service.update_config(config_dict)
        return {
            "success": True,
            "message": "Notification config updated",
            "config": notification_service.get_config()
        }
    except Exception as e:
        logger.error(f"Failed to update notification config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def create_test_notification(request: CreateNotificationRequest):
    """创建测试通知"""
    try:
        notif_type = NotificationType(request.type)
        priority = NotificationPriority(request.priority)
        
        notification = await notification_service.create_notification(
            notification_type=notif_type,
            title=request.title,
            message=request.message,
            priority=priority,
            data=request.data
        )
        
        if notification:
            return {
                "success": True,
                "notification": notification.to_dict()
            }
        else:
            return {
                "success": False,
                "message": "Notification type is disabled or quiet hours is active"
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid notification type or priority: {e}")
    except Exception as e:
        logger.error(f"Failed to create test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_notification_types():
    """获取所有通知类型"""
    return {
        "types": [
            {"value": t.value, "label": _get_type_label(t)}
            for t in NotificationType
        ]
    }


@router.get("/priorities")
async def get_notification_priorities():
    """获取所有通知优先级"""
    return {
        "priorities": [
            {"value": p.value, "label": _get_priority_label(p)}
            for p in NotificationPriority
        ]
    }


def _get_type_label(notification_type: NotificationType) -> str:
    labels = {
        NotificationType.PERFORMANCE_ALERT: "性能告警",
        NotificationType.DEVICE_STATUS: "设备状态",
        NotificationType.TEST_COMPLETE: "测试完成",
        NotificationType.REPORT_GENERATED: "报告生成",
        NotificationType.SYSTEM_MESSAGE: "系统消息",
        NotificationType.COLLABORATION: "协作通知",
        NotificationType.THRESHOLD_BREACH: "阈值告警"
    }
    return labels.get(notification_type, notification_type.value)


def _get_priority_label(priority: NotificationPriority) -> str:
    labels = {
        NotificationPriority.LOW: "低",
        NotificationPriority.MEDIUM: "中",
        NotificationPriority.HIGH: "高",
        NotificationPriority.CRITICAL: "严重"
    }
    return labels.get(priority, priority.value)
