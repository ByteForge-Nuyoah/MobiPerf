from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    serial: str = Field(..., description="设备序列号")
    name: Optional[str] = Field(None, description="设备名称")
    platform: str = Field(..., description="平台类型")
    model: Optional[str] = Field(None, description="设备型号")
    status: Optional[str] = Field(None, description="设备状态")


class AppInfo(BaseModel):
    package: str = Field(..., description="应用包名")
    name: str = Field(..., description="应用名称")


class DeviceListResponse(BaseModel):
    devices: List[DeviceInfo] = Field(..., description="设备列表")


class AppListResponse(BaseModel):
    apps: List[AppInfo] = Field(..., description="应用列表")


class SessionInfo(BaseModel):
    session_id: str = Field(..., description="会话ID")
    device_model: Optional[str] = Field(None, description="设备型号")
    device_serial: Optional[str] = Field(None, description="设备序列号")
    app_package: Optional[str] = Field(None, description="应用包名")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[int] = Field(None, description="测试时长(秒)")
    overall_score: Optional[float] = Field(None, description="综合评分")
    status: Optional[str] = Field(None, description="会话状态")


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")


class RecordFile(BaseModel):
    filename: str = Field(..., description="文件名")
    timestamp: int = Field(..., description="时间戳")
    package: str = Field(..., description="应用包名")
    size: int = Field(..., description="文件大小(字节)")
    url: str = Field(..., description="下载链接")


class RecordListResponse(BaseModel):
    files: List[RecordFile] = Field(..., description="文件列表")


class NotificationConfig(BaseModel):
    notification_type: str = Field(..., description="通知类型")
    enabled: bool = Field(..., description="是否启用")
    threshold: Optional[float] = Field(None, description="阈值")
    priority: str = Field(..., description="优先级")


class NotificationConfigResponse(BaseModel):
    configs: List[NotificationConfig] = Field(..., description="通知配置列表")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="错误信息")
    error_code: str = Field(..., description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="服务状态")
    database: str = Field(..., description="数据库状态")
    timestamp: str = Field(..., description="时间戳")
