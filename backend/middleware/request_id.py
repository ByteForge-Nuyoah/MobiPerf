import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger
from core.logging_config import RequestContext

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        
        RequestContext.set_request_id(request_id)
        
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        with logger.contextualize(request_id=request_id):
            logger.info(f"--> {request.method} {request.url.path}")
            
            response = await call_next(request)
            
            process_time = (time.time() - request.state.start_time) * 1000
            logger.info(
                f"<-- {request.method} {request.url.path} "
                f"| {response.status_code} | {process_time:.2f}ms"
            )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        RequestContext.clear_request_id()
        
        return response
