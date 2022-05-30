import ssl
from functools import partial
from os import getenv
from typing import Any, Dict, List, Optional, Sequence, Union, overload
from typing_extensions import Annotated
import requests
import uvicorn
import uvicorn.config
from fastapi import FastAPI
from pydantic import BaseModel, Field

CONFIG_FILE = getenv("CONFIG_FILE", "./config.yaml")


class AppConfig(BaseModel):
    debug: bool = False
    title: str = "FastAPI"
    description: str = ""
    version: str = "0.1.0"
    openapi_url: Optional[str] = "/openapi.json"
    openapi_tags: Optional[List[Dict[str, Any]]] = None
    servers: Optional[List[Dict[str, Union[str, Any]]]] = None
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect"
    swagger_ui_init_oauth: Optional[Dict[str, Any]] = None
    terms_of_service: Optional[str] = None
    contact: Optional[Dict[str, Union[str, Any]]] = None
    license_info: Optional[Dict[str, Union[str, Any]]] = None
    openapi_prefix: str = ""
    root_path: str = ""
    root_path_in_servers: bool = True
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None
    deprecated: Optional[bool] = None
    include_in_schema: bool = True


class ServingConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    uds: Optional[str] = None
    fd: Optional[int] = None
    loop: uvicorn.config.LoopSetupType = "auto"
    http: uvicorn.config.HTTPProtocolType = "auto"
    ws: uvicorn.config.WSProtocolType = "auto"
    ws_max_size: int = 16 * 1024 * 1024
    ws_ping_interval: Optional[float] = 20
    ws_ping_timeout: Optional[float] = 20
    lifespan: uvicorn.config.LifespanType = "auto"
    env_file: Optional[str] = None
    log_config: Optional[Union[dict, str]] = uvicorn.config.LOGGING_CONFIG
    log_level: Optional[Union[str, int]] = None
    access_log: bool = True
    use_colors: Optional[bool] = None
    interface: uvicorn.config.InterfaceType = "auto"
    debug: bool = False
    reload: bool = False
    reload_dirs: Optional[Union[List[str], str]] = None
    reload_delay: Optional[float] = None
    reload_includes: Optional[Union[List[str], str]] = None
    reload_excludes: Optional[Union[List[str], str]] = None
    workers: Optional[int] = None
    proxy_headers: bool = True
    server_header: bool = True
    date_header: bool = True
    forwarded_allow_ips: Optional[str] = None
    root_path: str = ""
    limit_concurrency: Optional[int] = None
    limit_max_requests: Optional[int] = None
    backlog: int = 2048
    timeout_keep_alive: int = 5
    timeout_notify: int = 30
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile_password: Optional[str] = None
    ssl_version: int = uvicorn.config.SSL_PROTOCOL_VERSION
    ssl_cert_reqs: int = ssl.CERT_NONE
    ssl_ca_certs: Optional[str] = None
    ssl_ciphers: str = "TLSv1"
    headers: Optional[List[List[str]]] = None
    factory: bool = False


class MergeConfig(BaseModel):
    upstreams: list[str]
    override: Dict[str, Any] = {}


class Config(BaseModel):
    app: AppConfig = AppConfig()
    serving: ServingConfig = ServingConfig()
    merge: MergeConfig
    _endpoint: Annotated[Optional[str], Field(alias="endpoint")] = None

    @property
    def endpoint(self):
        if self._endpoint is not None:
            return self._endpoint
        host = self.serving.host
        if host == "0.0.0.0":
            host = "localhost"

        return f"http://{host}:{self.serving.port}"


@overload
def merge(source: list, target: list) -> list:
    ...


@overload
def merge(source: dict, target: dict) -> dict:
    ...


@overload
def merge(source: Any, target: Any) -> Any:
    ...


def merge(source: dict | list | Any, target: dict | list | Any):
    if isinstance(source, dict | list):
        source = source.copy()
    if isinstance(source, dict) and isinstance(target, dict):
        for key, value in target.items():
            source[key] = merge(source.get(key, None), value)
        return source
    if isinstance(source, list) and isinstance(target, list):
        return source + target
    return target


cfg = Config.parse_file(CONFIG_FILE)

app = FastAPI(**cfg.app.dict())


openapi_original = app.openapi


def openapi():
    source = {}

    for upstream in cfg.merge.upstreams:
        target: dict = requests.get(upstream).json()
        source = merge(source, target)
    source = merge(source, openapi_original())
    source.update(cfg.merge.override)

    return source


app.openapi = openapi

uvicorn.run(app, **cfg.serving.dict())  # type: ignore
