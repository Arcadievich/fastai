import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from itertools import count
from pathlib import Path

import anyio
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


SITE = SiteResponse(
    id=1,
    title='Фан клуб Домино',
    prompt='Сайт любителей играть в домино',
    htmlCodeUrl='http://dvmn.org',
    htmlCodeDownloadUrl='http://example.com/media/index.html?response-content-disposition=attachment',
    screenshotUrl='http://example.com/media/index.png',
    createdAt=datetime(2025, 6, 15, 18, 29, 56),
    updatedAt=datetime(2026, 6, 15, 18, 29, 56),
)

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


@sites_router.get(
    '/sites/my',
    summary='Получить список сгенерированных сайтов текущего пользователя',
    response_model=GeneratedSitesResponse,
)
def mock_get_my_sites():
    sites = []
    for site_info in SITES.values():
        sites.append(SiteResponse(
            id=site_info['id'],
            title=site_info['title'],
            prompt=site_info['prompt'],
            htmlCodeUrl='/generated_sites/index.html',
            htmlCodeDownloadUrl='/generated_sites/index.html?response-content-disposition=attachment',
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
        'title': payload.title,
        'prompt': payload.prompt,
        'html': None,
        'createdAt': now,
        'updatedAt': now,
    }

    return SiteResponse(
        id=site_id,
        title=initial_title,
        prompt=payload.prompt,
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

                output_path = Path('frontend/generated_sites') / 'index.html'
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(html, encoding='utf-8')

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
    return SiteResponse(
        id=site_info['id'],
        title=site_info['title'],
        prompt=site_info['prompt'],
        htmlCodeUrl='/generated_sites/index.html',
        htmlCodeDownloadUrl='/generated_sites/index.html?response-content-disposition=attachment',
        createdAt=site_info['createdAt'],
        updatedAt=site_info['updatedAt'],
    )


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(sites_router)
app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
