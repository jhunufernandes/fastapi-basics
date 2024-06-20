import functools
import time
import typing

import fastapi
import pydantic


"""
    Execution order (top to bottom):
        custom_dependency before: <starlette.requests.Request object at 0x1054e39e0>
        before_func: () {'dep': None}
        endpoint
        after_func: (CustomModelA(field_a='field_a'),) {'dep': None}
        custom_dependency after: <starlette.requests.Request object at 0x1054e39e0>
"""

req_sample: dict[str, typing.Any] = {
    "scope": {
        "type": "http",
        "asgi": {
            "version": "3.0",
            "spec_version": "2.4"
        },
        "http_version": "1.1",
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 60753),
        "scheme": "http",
        "root_path": "",
        "headers": [
            (b"host", b"localhost:8000"),
            (b"sec-fetch-site", b"same-origin"),
            (b"accept-encoding", b"gzip, deflate"),
            (b"connection", b"keep-alive"),
            (b"sec-fetch-mode", b"cors"),
            (b"accept", b"application/json"),
            (b"user-agent", b"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"),
            (b"referer", b"http://localhost:8000/docs"),
            (b"sec-fetch-dest", b"empty"),
            (b"accept-language", b"pt-BR,pt;q=0.9")
        ],
        "state": {},
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "app": """ <fastapi.applications.FastAPI object at 0x1097b4890> """,
        "starlette.exception_handlers": (
            {
                """ <class "starlette.exceptions.HTTPException">: <function http_exception_handler at 0x108613b00> """,
                """ <class "starlette.exceptions.WebSocketException">: <bound method ExceptionMiddleware.websocket_exception of <starlette.middleware.exceptions.ExceptionMiddleware object at 0x109755250>> """,
                """ <class "fastapi.exceptions.RequestValidationError">: <function request_validation_exception_handler at 0x108613ba0> """,
                """ <class "fastapi.exceptions.WebSocketRequestValidationError">: <function websocket_request_validation_exception_handler at 0x108613c40> """
            },
            {}
        ),
        "router": """ <fastapi.routing.APIRouter object at 0x1097b4830> """,
        "endpoint": """ <function endpoint at 0x1097b1d00> """,
        "path_params": {},
        "route": """ APIRoute(
            path="/",
            name="endpoint",
            methods=[
                "GET",
                "POST"
            ]
        ) """
    },
    "_receive": """ <bound method RequestResponseCycle.receive of <uvicorn.protocols.http.httptools_impl.RequestResponseCycle object at 0x1097b5d60>> """,
    "_send": """ <function wrap_app_handling_exceptions.<locals>.wrapped_app.<locals>.sender at 0x1097b2480> """,
    "_stream_consumed": False,
    "_is_disconnected": False,
    "_form": None,
    "_query_params": """ QueryParams("") """,
    "_headers": """ Headers({
        "host": "localhost:8000",
        "sec-fetch-site": "same-origin",
        "accept-encoding": "gzip, deflate",
        "connection": "keep-alive",
        "sec-fetch-mode": "cors",
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "referer": "http://localhost:8000/docs",
        "sec-fetch-dest": "empty",
        "accept-language": "pt-BR,pt;q=0.9"
    }) """,
    "_cookies": {}
}


res_sample: dict[str, typing.Any] = {
    'status_code': None,
    'background': None,
    'body': b'',
    'raw_headers': [],
    '_headers': """ MutableHeaders({}) """
}


class Event(pydantic.BaseModel):
    method: str
    endpoint: str



def custom_dependency(req: fastapi.Request, res: fastapi.Response):
    print(f"custom_dependency before: {req}")
    yield
    # breakpoint()
    print(f"custom_dependency after: {req}")


def before_func(*args: typing.Any, **kwargs: typing.Any):
    print(f"before_func: {args} {kwargs}")
    return


def after_func(*args: typing.Any, **kwargs: typing.Any):
    print(f"after_func: {args} {kwargs}")
    return


def custom_decorator(
    original_func: typing.Callable[..., typing.Any],
    before_func: typing.Callable[..., typing.Any] = lambda *args, **kwargs: None,
    after_func: typing.Callable[..., typing.Any] = lambda *args, **kwargs: None,
) -> typing.Callable[..., typing.Any]:
    @functools.wraps(original_func)
    async def wrapper(*args: typing.Any, **kwargs: typing.Any):
        before_func(*args, **kwargs)
        result = await original_func(*args, **kwargs)
        after_func(result, *args, **kwargs)
        return result

    return wrapper


class CustomModelA(pydantic.BaseModel):
    field_a: str = "field_a"


class CustomModelB(CustomModelA):
    field_b: str = "field_b"


@custom_decorator
async def endpoint_abc(dep: typing.Annotated[typing.Any, fastapi.Depends(custom_dependency)]) -> CustomModelA:
    print("endpoint")
    return CustomModelA()


app = fastapi.FastAPI()


@app.middleware("http")
async def add_process_time_header(request: fastapi.Request, call_next: typing.Callable[..., typing.Any]) -> fastapi.Response:
    # start_time = time.time()
    response = await call_next(request)
    # process_time = time.time() - start_time
    # response.headers["X-Process-Time"] = str(process_time)
    # breakpoint()
    return response


router = fastapi.APIRouter()


router.add_api_route(
    path="/",
    endpoint=custom_decorator(endpoint_abc, before_func, after_func),
    response_model=CustomModelB,
    methods=["GET", "POST"],
    status_code=200,
    dependencies=[],
)


app.include_router(router)
