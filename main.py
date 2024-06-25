import functools
import typing

import fastapi
import fastapi.middleware
import pydantic
import starlette
import starlette.middleware
import starlette.middleware.base
import uvicorn
import uvicorn.middleware
import uvicorn.middleware.message_logger

"""
    Execution order (top to bottom):
        custom_middleware before
        dependency_in_app before
        dependency_in_router before
        dependency_in_endpoint before
        custom_dependency before
        custom_dependency_with_sub before
        before_func: () {'dep': None}
        endpoint
        after_func: (CustomModelA(field_a='field_a'),) {'dep': None}
        custom_dependency_with_sub after
        custom_dependency after
        dependency_in_endpoint after
        dependency_in_router after
        dependency_in_app after
        custom_middleware after
"""


async def custom_dependency():
    print("custom_dependency before")
    yield
    print("custom_dependency after")


async def custom_dependency_with_sub(dep_a: typing.Annotated[typing.Any, fastapi.Depends(custom_dependency)]):
    print("custom_dependency_with_sub before")
    yield
    print("custom_dependency_with_sub after")


async def dependency_in_app():
    print("dependency_in_app before")
    yield
    print("dependency_in_app after")


async def dependency_in_router():
    print("dependency_in_router before")
    yield
    print("dependency_in_router after")


async def dependency_in_endpoint():
    print("dependency_in_endpoint before")
    yield
    print("dependency_in_endpoint after")


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
async def endpoint(dep: typing.Annotated[typing.Any, fastapi.Depends(custom_dependency_with_sub)]) -> CustomModelA:
    print("endpoint")
    return CustomModelA()


app = fastapi.FastAPI(
    dependencies=[fastapi.Depends(dependency_in_app)],
    # middleware=[CustomMiddleware]
)


router = fastapi.APIRouter(dependencies=[fastapi.Depends(dependency_in_router)])


router.add_api_route(
    path="/",
    endpoint=custom_decorator(endpoint, before_func, after_func),
    response_model=CustomModelB,
    methods=["GET"],
    status_code=200,
    dependencies=[fastapi.Depends(dependency_in_endpoint)],
)


app.include_router(router)


@app.middleware("http")
async def custom_middleware_func(request: fastapi.Request, call_next: typing.Callable[..., typing.Any]) -> fastapi.Response:
    print(f"custom_middleware_decorator before: {request}")
    response: fastapi.Response = await call_next(request)
    print(f"custom_middleware_decorator after: {request} {response}")
    return response


class CustomMiddlewareClass(starlette.middleware.base.BaseHTTPMiddleware):
    # def __init__(self, app: fastapi.FastAPI, some_attribute: str | None = None):
    #     super().__init__(app)
    #     self.some_attribute = some_attribute

    async def dispatch(self, request: fastapi.Request, call_next: typing.Callable[..., typing.Any]):
        print(f"custom_middleware_class 1 before: {request}")
        response = await call_next(request)
        print(f"custom_middleware_class 1 after: {request} {response}")
        return response


from fastapi import Request

class MyMiddleware:
    # def __init__(
    #         self,
    #         some_attribute: str,
    # ):
    #     self.some_attribute = some_attribute

    async def __call__(self, request: Request, call_next: typing.Callable[..., typing.Any]):
        print(f"custom_middleware_class 2 before: {request}")
        response = await call_next(request)
        print(f"custom_middleware_class 2 after: {request} {response}")
        return response



app.add_middleware(starlette.middleware.base.BaseHTTPMiddleware, dispatch=MyMiddleware())
app.add_middleware(CustomMiddlewareClass)
# app.add_middleware(uvicorn.middleware.message_logger.MessageLoggerMiddleware)
