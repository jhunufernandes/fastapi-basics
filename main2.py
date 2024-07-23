
from typing import Any, Annotated, Literal

from httpx import post
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.security import APIKeyCookie, APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
from pydantic.dataclasses import dataclass


class Client:
    def __init__(self) -> None:
        self.url = "http://localhost:8000/validate"

    def call(self, headers: dict[str, Any], json: dict[str, Any]) -> None:
        post(self.url, headers=headers, json=json)


#######################################################################################################################


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
    client = Client()

    def __init__(self, api_key: APIKey, type: Literal["header", "cookie", "query"], service: str) -> None:
        scheme = getattr(APIKeyScheme, type)
        self.type = type
        self.service = service
        self.scheme = scheme(name=api_key.name, scheme_name=api_key.scheme_name, description=api_key.description, auto_error=api_key.auto_error)

    @property
    def dependency(self):
        def api_key_auth(key: Annotated[str, Depends(self.scheme)], request: Request):
            print("api_key_auth")
            headers = {
                "X-API-Key": key
            }
            json = {
                "service": self.service,
                "resource": request.url.path,
                "auth": {
                    "": f"api_key_{self.type}"
                }
            }
            self.client.call(headers=headers, json=json)

        return Depends(api_key_auth)


api_key = APIKey("X-API-Key")
api_key_auth = APIKeyAuth(api_key, "header", "resource_example")
api_key_auth_dependency = api_key_auth.dependency


#######################################################################################################################


dependencies = [api_key_auth_dependency]
router = APIRouter()


class CustomModelA(BaseModel):
    field_a: str = "field_a"


class CustomModelB(CustomModelA):
    field_b: str = "field_b"


async def endpoint() -> CustomModelA:
    print("endpoint")
    return CustomModelA()


router.add_api_route(
    path="/resource",
    endpoint=endpoint,
    response_model=CustomModelB,
    methods=["GET"],
    status_code=200,
    dependencies=dependencies,
)

#######################################################################################################################


class Auth(BaseModel):
    method: Literal["api_key_header"]


class Authorize(BaseModel):
    service: str
    resource: str
    auth: Auth


async def authorize(authorize: Authorize) -> None:
    print("authorize")
    print(authorize.model_dump_json())
    return


router.add_api_route(
    path="/authorize",
    endpoint=authorize,
    methods=["POST"],
)


#######################################################################################################################


app = FastAPI()
app.include_router(router)
