
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, FastAPI
from fastapi.security import APIKeyCookie, APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
from pydantic.dataclasses import dataclass


@dataclass
class APIKey:
    name: str
    scheme_name: str | None = None
    description: str | None = None
    auto_error: bool = True


@dataclass
class APIKeyScheme:
    header = APIKeyHeader
    cookie = APIKeyCookie
    query = APIKeyQuery


class APIKeyAuth:
    def __init__(self, api_key: APIKey, type: Literal["header", "cookie", "query"]) -> None:
        scheme = getattr(APIKeyScheme, type)
        self.scheme = scheme(name=api_key.name, scheme_name=api_key.scheme_name, description=api_key.description, auto_error=api_key.auto_error)

    @property
    def dependency(self):
        def api_key_auth(key: Annotated[str, Depends(self.scheme)]):
            print(f"{self.scheme.model.name}: {key}")
            print(api_key_auth)
            return

        return Depends(api_key_auth)


api_key = APIKey("X-API-Key")
api_key_auth = APIKeyAuth(api_key, "header")
api_key_auth_dependency = api_key_auth.dependency


dependencies = [api_key_auth_dependency]
router = APIRouter(dependencies=dependencies)


class CustomModelA(BaseModel):
    field_a: str = "field_a"


class CustomModelB(CustomModelA):
    field_b: str = "field_b"


async def endpoint() -> CustomModelA:
    print("endpoint")
    return CustomModelA()


router.add_api_route(
    path="/",
    endpoint=endpoint,
    response_model=CustomModelB,
    methods=["GET"],
    status_code=200,
)


async def validate() -> None:
    print("validate")
    return None


router.add_api_route(
    path="/validate",
    endpoint=validate,
    # response_model=CustomModelB,
    methods=["POST"],
    # status_code=200,
)
app = FastAPI()
app.include_router(router)

