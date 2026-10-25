import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from itertools import count
from pathlib import Path

import aioboto3
import anyio
from aiobotocore.config import AioConfig
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
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


async def async_stream_plug_html():
    html = Path('frontend/plug.html').read_text(encoding='utf-8')

    for one_len in range(0, len(html), 160):
        yield html[one_len:one_len + 160]
        await asyncio.sleep(0.3)


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


def build_s3_urls(key: str) -> tuple[str, str]:
    base = f'{app_settigns.s3.endpoint_url}/{app_settigns.s3.bucket_name}/{key}'
    download = f'{base}?response-content-disposition=attachment'
    return base, download


@sites_router.get(
    '/sites/my',
    summary='Получить список сгенерированных сайтов текущего пользователя',
    response_model=GeneratedSitesResponse,
)
def mock_get_my_sites():
    sites = []
    for site_info in SITES.values():
        html_url, download_url = build_s3_urls('index.html')
        sites.append(SiteResponse(
            id=site_info['id'],
            title=site_info['title'],
            prompt=site_info['prompt'],
            htmlCodeUrl=html_url,
            htmlCodeDownloadUrl=download_url,
            createdAt=site_info['createdAt'],
            updatedAt=site_info['updatedAt'],
        ))
    return {'sites': sites}


@sites_router.post(
    '/sites/create',
    summary='Создать сайт',
    response_model=SiteResponse,
)
def mock_create_site(payload: CreateSiteRequest):
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
    return SiteResponse(
        id=site_id,
        title=initial_title,
        prompt=payload.prompt,
        htmlCodeUrl=html_url,
        htmlCodeDownloadUrl=download_url,
        createdAt=now,
        updatedAt=now,
    )


@sites_router.post(
    '/sites/{site_id}/generate',
    summary='Сгенерировать HTML-код сайта',
)
async def mock_generate_site(site_id: int, payload: SiteGenerationRequest):
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

                try:
                    session: aioboto3.Session = app.state.s3_session
                    s3 = app_settigns.s3
                    config = AioConfig(
                        max_pool_connections=s3.max_connections,
                        connect_timeout=s3.connect_timeout,
                        read_timeout=s3.read_timeout,
                        proxies={},
                    )
                    async with session.client(
                        's3',
                        endpoint_url=s3.endpoint_url,
                        aws_access_key_id=s3.access_key.get_secret_value(),
                        aws_secret_access_key=s3.secret_key.get_secret_value(),
                        config=config,
                        region_name='us-east-1',
                    ) as s3_client:  # pyright: ignore[reportGeneralTypeIssues]
                        content_type = 'text/html'
                        key = 'index.html'
                        await s3_client.put_object(
                            Bucket=s3.bucket_name,
                            Key=key,
                            Body=html.encode('utf-8'),
                            ContentType=content_type,
                            ContentDisposition='inline',
                        )
                        logger.info(f'HTML загружен в S3: {s3.bucket_name}/{key}')
                except Exception as e:
                    logger.error(f'Ошибка загрузки в S3: {e}')

                SITES[site_id]['html'] = html
                SITES[site_id]['title'] = title
                SITES[site_id]['updatedAt'] = datetime.utcnow()

    return StreamingResponse(stream_and_save(), media_type='text/plain')


@sites_router.get(
    '/sites/{site_id}',
    summary='Получить сайт',
    response_model=SiteResponse,
)
def mock_get_site(site_id: int):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail='Site not found')

    site_info = SITES[site_id]
    html_url, download_url = build_s3_urls('index.html')
    return SiteResponse(
        id=site_info['id'],
        title=site_info['title'],
        prompt=site_info['prompt'],
        htmlCodeUrl=html_url,
        htmlCodeDownloadUrl=download_url,
        createdAt=site_info['createdAt'],
        updatedAt=site_info['updatedAt'],
    )


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(sites_router)
app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
