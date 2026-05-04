import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.request_context import set_request_id

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        start = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start

            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            )

            return response
        
        except Exception:
            logger.exception(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path
                }
            )

            raise