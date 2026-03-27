from typing import Any, Dict, Optional


class MobiPerfException(Exception):
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class DeviceNotFoundError(MobiPerfException):
    def __init__(self, device_serial: str):
        super().__init__(
            message=f"设备未找到: {device_serial}",
            error_code="DEVICE_NOT_FOUND",
            details={"device_serial": device_serial}
        )


class DeviceConnectionError(MobiPerfException):
    def __init__(self, device_serial: str, reason: str = ""):
        super().__init__(
            message=f"设备连接失败: {device_serial}. {reason}",
            error_code="DEVICE_CONNECTION_ERROR",
            details={"device_serial": device_serial, "reason": reason}
        )


class DatabaseConnectionError(MobiPerfException):
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"数据库连接失败: {reason}",
            error_code="DATABASE_CONNECTION_ERROR",
            details={"reason": reason}
        )


class SessionNotFoundError(MobiPerfException):
    def __init__(self, session_id: str):
        super().__init__(
            message=f"测试会话未找到: {session_id}",
            error_code="SESSION_NOT_FOUND",
            details={"session_id": session_id}
        )


class InvalidParameterError(MobiPerfException):
    def __init__(self, parameter: str, reason: str = ""):
        super().__init__(
            message=f"参数错误: {parameter}. {reason}",
            error_code="INVALID_PARAMETER",
            details={"parameter": parameter, "reason": reason}
        )


class CollectionError(MobiPerfException):
    def __init__(self, device_serial: str, reason: str = ""):
        super().__init__(
            message=f"数据采集失败: {device_serial}. {reason}",
            error_code="COLLECTION_ERROR",
            details={"device_serial": device_serial, "reason": reason}
        )


class ReportGenerationError(MobiPerfException):
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"报告生成失败: {reason}",
            error_code="REPORT_GENERATION_ERROR",
            details={"reason": reason}
        )


class AuthenticationError(MobiPerfException):
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"认证失败: {reason}",
            error_code="AUTHENTICATION_ERROR",
            details={"reason": reason}
        )


class RateLimitError(MobiPerfException):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"请求过于频繁，请 {retry_after} 秒后重试",
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after}
        )
