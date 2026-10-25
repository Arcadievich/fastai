import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from itertools import count

import aioboto3
import anyio
import httpx
from aiobotocore.config import AioConfig
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient
from pydantic import BaseModel, EmailStr, Field

from env_settings import app_settigns

users_router = APIRouter(prefix='/frontend-api', tags=['Users'])
sites_router = APIRouter(prefix='/frontend-api', tags=['Sites'])


class UserDetailsResponse(BaseModel):
    profileId: int
    email: EmailStr
    username: str = Field(max_length=254)
    registeredAt: datetime
    updatedAt: datetime
    isActive: bool


class CreateSiteRequest(BaseModel):
    title: str | None = Field(default=None, max_length=128)
    prompt: str


class SiteGenerationRequest(BaseModel):
    prompt: str


class SiteResponse(BaseModel):
    id: int
    title: str
    htmlCodeUrl: str | None = None
    htmlCodeDownloadUrl: str | None = None
    screenshotUrl: str | None = None
    prompt: str
    createdAt: datetime
    updatedAt: datetime


class GeneratedSitesResponse(BaseModel):
    sites: list[SiteResponse]


SITES: dict[int, dict] = {}
_site_id_counter = count(1)

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

    app.state.s3_session = aioboto3.Session()

    async with (
        AsyncUnsplashClient.setup(
            app_settigns.unsplash.api_token.get_secret_value(),
            timeout=app_settigns.unsplash.timeout,
        ),
        AsyncDeepseekClient.setup(
            app_settigns.vsegpt.api_token.get_secret_value(),
            app_settigns.vsegpt.url,
            app_settigns.vsegpt.model,
        ),
    ):

        yield


def build_s3_urls(key: str) -> tuple[str, str]:
    base = f'{app_settigns.s3.endpoint_url}/{app_settigns.s3.bucket_name}/{key}'
    download = f'{base}?response-content-disposition=attachment'
    return base, download


async def save_site_files_to_s3(html: str, site_id: int):
    s3 = app_settigns.s3
    gotenberg = app_settigns.gotenberg

    config = AioConfig(
        max_pool_connections=s3.max_connections,
        connect_timeout=s3.connect_timeout,
        read_timeout=s3.read_timeout,
        proxies={},
    )

    try:
        session = aioboto3.Session()
        async with session.client(
            's3',
            endpoint_url=s3.endpoint_url,
            aws_access_key_id=s3.access_key.get_secret_value(),
            aws_secret_access_key=s3.secret_key.get_secret_value(),
            config=config,
            region_name='us-east-1',
        ) as s3_client:  # pyright: ignore[reportGeneralTypeIssues]
            await s3_client.put_object(
                Bucket=s3.bucket_name,
                Key='index.html',
                Body=html.encode('utf-8'),
                ContentType='text/html',
                ContentDisposition='inline',
            )
            logger.info(f'HTML загружен в S3: {s3.bucket_name}/index.html')

            try:
                logger.info(f'[Gotenberg] Генерация скриншота для сайта {site_id}...')

                async with httpx.AsyncClient(
                    base_url=gotenberg.api_url,
                    timeout=gotenberg.timeout,
                    limits=httpx.Limits(max_connections=gotenberg.max_connections),
                ) as client:
                    screenshot_bytes = await ScreenshotHTMLRequest(
                        index_html=html,
                        width=gotenberg.width,
                        format=gotenberg.format,
                        wait_delay=gotenberg.wait_delay,
                    ).asend(client)

                    await s3_client.put_object(
                        Bucket=s3.bucket_name,
                        Key='index.png',
                        Body=screenshot_bytes,
                        ContentType='image/png',
                        ContentDisposition='inline',
                    )
                    logger.info(f'Скриншот загружен в S3: {s3.bucket_name}/index.png')
            except GotenbergServerError as e:
                logger.error(f'Ошибка Gotenberg: {e}')
            except Exception as e:
                logger.error(f'Ошибка генерации скриншота: {e}')

    except Exception as e:
        logger.error(f'Ошибка загрузки в S3: {e}')


@users_router.get(
        '/users/me',
        summary='Получить учетные данные пользователя',
        response_model=UserDetailsResponse,
)
def mock_get_user():
    mock_user_info = {
        'email': 'user_274@mail.ru',
        'isActive': True,
        'profileId': '1',
        'registeredAt': '2025-06-15T18:29:56+00:00',
        'updatedAt': '2025-06-15T18:29:56+00:00',
        'username': 'arcadievich',
    }

    return mock_user_info


@sites_router.get(
    '/sites/my',
    summary='Получить список сгенерированных сайтов текущего пользователя',
    response_model=GeneratedSitesResponse,
)
def get_my_sites():
    sites = []
    for site_info in SITES.values():
        html_url, download_url = build_s3_urls('index.html')
        image_url, _ = build_s3_urls('index.png')
        sites.append(SiteResponse(
            id=site_info['id'],
            title=site_info['title'],
            prompt=site_info['prompt'],
            htmlCodeUrl=html_url,
            htmlCodeDownloadUrl=download_url,
            screenshotUrl=image_url,
            createdAt=site_info['createdAt'],
            updatedAt=site_info['updatedAt'],
        ))
    return {'sites': sites}


@sites_router.post(
    '/sites/create',
    summary='Создать сайт',
    response_model=SiteResponse,
)
def create_site(payload: CreateSiteRequest):
    now = datetime.utcnow()
    site_id = next(_site_id_counter)

    initial_title = payload.title or ''

    SITES[site_id] = {
        'id': site_id,
        'title': initial_title,
        'prompt': payload.prompt,
        'html': None,
        'createdAt': now,
        'updatedAt': now,
    }

    html_url, download_url = build_s3_urls('index.html')
    image_url, _ = build_s3_urls('index.png')
    return SiteResponse(
        id=site_id,
        title=initial_title,
        prompt=payload.prompt,
        htmlCodeUrl=html_url,
        htmlCodeDownloadUrl=download_url,
        screenshotUrl=image_url,
        createdAt=now,
        updatedAt=now,
    )


@sites_router.post(
    '/sites/{site_id}/generate',
    summary='Сгенерировать HTML-код сайта',
)
async def generate_site(site_id: int, payload: SiteGenerationRequest):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail='Site not found')

    prompt = payload.prompt or SITES[site_id]['prompt']

    async def stream_and_save():
        generator = AsyncPageGenerator(debug_mode=app_settigns.debug)
        chunks: list[str] = []

        try:
            async for chunk in generator(prompt):
                if isinstance(chunk, list):
                    text = ''.join(str(c) for c in chunk)
                else:
                    text = chunk

                chunks.append(text)
                yield text
        finally:
            with anyio.CancelScope(shield=True):
                html = ''.join(chunks)
                title = generator.html_page.title or SITES[site_id]['title']

                await save_site_files_to_s3(html, site_id)

                SITES[site_id]['html'] = html
                SITES[site_id]['title'] = title
                SITES[site_id]['updatedAt'] = datetime.utcnow()

    return StreamingResponse(stream_and_save(), media_type='text/plain')


@sites_router.get(
    '/sites/{site_id}',
    summary='Получить сайт',
    response_model=SiteResponse,
)
def get_site(site_id: int):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail='Site not found')

    site_info = SITES[site_id]
    html_url, download_url = build_s3_urls('index.html')
    image_url, _ = build_s3_urls('index.png')
    return SiteResponse(
        id=site_info['id'],
        title=site_info['title'],
        prompt=site_info['prompt'],
        htmlCodeUrl=html_url,
        htmlCodeDownloadUrl=download_url,
        screenshotUrl=image_url,
        createdAt=site_info['createdAt'],
        updatedAt=site_info['updatedAt'],
    )


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(sites_router)
app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
