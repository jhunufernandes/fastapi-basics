import functools
import typing

import fastapi
import pydantic


"""
    Execution order (top to bottom):
        dependency_in_app before
        dependency_in_router before
        dependency_in_endpoint before
        custom_dependency before
        custom_dependency_with_sub before
        before_func
        endpoint
        after_func
        custom_dependency_with_sub after
        custom_dependency after
        dependency_in_endpoint after
        dependency_in_router after
"""


def custom_dependency():
    print("custom_dependency before")
    yield
    print("custom_dependency after")


def custom_dependency_with_sub(dep_a: typing.Annotated[typing.Any, fastapi.Depends(custom_dependency)]):
    print("custom_dependency_with_sub before")
    yield
    print("custom_dependency_with_sub after")


def dependency_in_app():
    print("dependency_in_app before")
    yield
    print("dependency_in_app after")


def dependency_in_router():
    print("dependency_in_router before")
    yield
    print("dependency_in_router after")


def dependency_in_endpoint():
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


app = fastapi.FastAPI(dependencies=[fastapi.Depends(dependency_in_app)])


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
