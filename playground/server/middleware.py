"""the http server for NPI backend"""
import time

from fastapi import Request, Response

__AUTH_TOKEN = 'default'
__AUTH_ENABLED = False


async def auth(request: Request, call_next):
    """the middleware for authentication"""
    start_time = time.time()
    if __AUTH_ENABLED and ('authorization' not in request.headers or
                           __AUTH_TOKEN != request.headers['authorization']):
        return Response('Unauthorized', status_code=401)
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
