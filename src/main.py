import json
import logging
from contextlib import AsyncExitStack, asynccontextmanager

import aioboto3
import httpx
from aiobotocore.config import AioConfig
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from html_page_generator import AsyncDeepseekClient, AsyncUnsplashClient

from env_settings import app_settigns
from routers import sites_router, users_router

logger = logging.getLogger('uvicorn.error')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        'Загруженные настройки:\n%s',
        json.dumps(
            app_settigns.model_dump(),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
    )

    s3 = app_settigns.s3
    gotenberg = app_settigns.gotenberg

    app.state.s3_settings = s3
    app.state.gotenberg_settings = gotenberg

    config = AioConfig(
        max_pool_connections=s3.max_connections,
        connect_timeout=s3.connect_timeout,
        read_timeout=s3.read_timeout,
        proxies={},
    )

    async with AsyncExitStack() as stack:
        session = aioboto3.Session()
        s3_client = await stack.enter_async_context(
            session.client(
                's3',
                endpoint_url=str(s3.endpoint_url),
                aws_access_key_id=s3.access_key.get_secret_value(),
                aws_secret_access_key=s3.secret_key.get_secret_value(),
                config=config,
                region_name='us-east-1',
            ),  # pyright: ignore[reportArgumentType]
        )
        app.state.s3_client = s3_client

        http_client = await stack.enter_async_context(
            httpx.AsyncClient(
                base_url=str(gotenberg.api_url),
                timeout=gotenberg.timeout,
                limits=httpx.Limits(max_connections=gotenberg.max_connections),
            ),
        )
        app.state.gotenberg_client = http_client

        async with (
            AsyncUnsplashClient.setup(
                app_settigns.unsplash.api_token.get_secret_value(),
                timeout=app_settigns.unsplash.timeout,
            ),
            AsyncDeepseekClient.setup(
                app_settigns.vsegpt.api_token.get_secret_value(),
                str(app_settigns.vsegpt.url),
                app_settigns.vsegpt.model,
            ),
        ):
            yield


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(sites_router)

app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
