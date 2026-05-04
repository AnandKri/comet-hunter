from contextvars import ContextVar

request_id_context = ContextVar("request_id", default=None)

def set_request_id(request_id: str):
    request_id_context.set(request_id)

def get_request_id() -> str:
    return request_id_context.get()