from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import logging
from core.exceptions import MobiPerfException


async def mobiperf_exception_handler(request: Request, exc: MobiPerfException):
    logger.error(f"MobiPerf Exception: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.to_dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.error(f"Validation Error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "数据验证失败",
            "error_code": "VALIDATION_ERROR",
            "details": {"errors": errors}
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unexpected error: {str(exc)}")
    is_debug = logger._core.handlers and any(
        h.levelno <= logging.DEBUG for h in logger._core.handlers.values()
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "服务器内部错误",
            "error_code": "INTERNAL_ERROR",
            "details": {"message": str(exc)} if is_debug else {}
        }
    )
