import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

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
    title: str
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
    htmlCodeUrl='http://google.com',
    htmlCodeDownloadUrl='http://example.com/media/index.html?response-content-disposition=attachment',
    screenshotUrl='http://example.com/media/index.png',
    createdAt=datetime(2025, 6, 15, 18, 29, 56),
    updatedAt=datetime(2026, 6, 15, 18, 29, 56),
)


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
    return {'sites': [SITE]}


@sites_router.post(
    '/sites/create',
    summary='Создать сайт',
    response_model=SiteResponse,
)
def mock_create_site(payload: CreateSiteRequest):
    return SiteResponse(
        id=1,
        title=payload.title,
        prompt=payload.prompt,
        createdAt=datetime(2026, 6, 15, 18, 29, 56),
        updatedAt=datetime(2026, 6, 15, 18, 29, 56),
    )


@sites_router.post(
    '/sites/{site_id}/generate',
    summary='Сгенерировать HTML-код сайта',
)
async def mock_generate_site(site_id: int, payload: SiteGenerationRequest):
    return StreamingResponse(async_stream_plug_html(), media_type='text/plain')


@sites_router.get(
    '/sites/{site_id}',
    summary='Получить сайт',
    response_model=SiteResponse,
)
def mock_get_site(site_id: int):
    return SITE


app = FastAPI()

app.include_router(users_router)
app.include_router(sites_router)
app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
