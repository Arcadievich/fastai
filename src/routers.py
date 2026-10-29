from datetime import datetime, timezone
from functools import partial

import anyio
from aiobotocore.client import AioBaseClient
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from html_page_generator import AsyncPageGenerator
from httpx import AsyncClient

from env_settings import GotenbergSettings, S3Settings, app_settigns
from schemas import (
    CreateSiteRequest,
    GeneratedSitesResponse,
    SiteGenerationRequest,
    SiteResponse,
    UserDetailsResponse,
)
from storage import SITES, build_s3_urls, generate_site_id, publish_site

users_router = APIRouter(prefix='/frontend-api', tags=['Users'])
sites_router = APIRouter(prefix='/frontend-api', tags=['Sites'])


async def stream_and_save(
    prompt: str,
    site_id: int,
    s3_client: AioBaseClient,
    s3_settings: S3Settings,
    gotenberg_client: AsyncClient,
    gotenberg_settings: GotenbergSettings,
):
    generator = AsyncPageGenerator(debug_mode=app_settigns.debug)
    chunks: list[str] = []

    try:
        with anyio.CancelScope(shield=True):
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

            await publish_site(
                s3_client=s3_client,
                s3_settings=s3_settings,
                gotenberg_client=gotenberg_client,
                gotenberg_settings=gotenberg_settings,
                html=html,
                site_id=site_id,
            )

            SITES[site_id]['html'] = html
            SITES[site_id]['title'] = title
            SITES[site_id]['updated_at'] = datetime.now(timezone.utc)


@users_router.get(
    '/users/me',
    summary='Получить учетные данные пользователя',
    response_model=UserDetailsResponse,
)
def mock_get_user():
    return {
        'email': 'user_274@mail.ru',
        'is_active': True,
        'profile_id': 1,
        'registered_at': '2025-06-15T18:29:56+00:00',
        'updated_at': '2025-06-15T18:29:56+00:00',
        'username': 'arcadievich',
    }


@sites_router.get(
    '/sites/my',
    summary='Получить список сгенерированных сайтов текущего пользователя',
    response_model=GeneratedSitesResponse,
)
def get_my_sites(request: Request):
    s3_settings = request.app.state.s3_settings
    sites = []
    for site_info in SITES.values():
        html_url, download_url = build_s3_urls(s3_settings, 'index.html')
        image_url, _ = build_s3_urls(s3_settings, 'index.png')
        sites.append(SiteResponse(
            id=site_info['id'],
            title=site_info['title'],
            prompt=site_info['prompt'],
            html_code_url=html_url,
            html_code_download_url=download_url,
            screenshot_url=image_url,
            created_at=site_info['created_at'],
            updated_at=site_info['updated_at'],
        ))
    return {'sites': sites}


@sites_router.post(
    '/sites/create',
    summary='Создать сайт',
    response_model=SiteResponse,
)
def create_site(payload: CreateSiteRequest, request: Request):
    s3_settings = request.app.state.s3_settings
    now = datetime.now(timezone.utc)
    site_id = generate_site_id()

    initial_title = payload.title or ''

    SITES[site_id] = {
        'id': site_id,
        'title': initial_title,
        'prompt': payload.prompt,
        'html': None,
        'created_at': now,
        'updated_at': now,
    }

    html_url, download_url = build_s3_urls(s3_settings, 'index.html')
    image_url, _ = build_s3_urls(s3_settings, 'index.png')
    return SiteResponse(
        id=site_id,
        title=initial_title,
        prompt=payload.prompt,
        html_code_url=html_url,
        html_code_download_url=download_url,
        screenshot_url=image_url,
        created_at=now,
        updated_at=now,
    )


@sites_router.post(
    '/sites/{site_id}/generate',
    summary='Сгенерировать HTML-код сайта',
)
async def generate_site(site_id: int, payload: SiteGenerationRequest, request: Request):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail='Site not found')

    prompt = payload.prompt or SITES[site_id]['prompt']

    s3_client = request.app.state.s3_client
    s3_settings = request.app.state.s3_settings
    gotenberg_client = request.app.state.gotenberg_client
    gotenberg_settings = request.app.state.gotenberg_settings

    response_generator = partial(
        stream_and_save,
        prompt=prompt,
        site_id=site_id,
        s3_client=s3_client,
        s3_settings=s3_settings,
        gotenberg_client=gotenberg_client,
        gotenberg_settings=gotenberg_settings,
    )

    return StreamingResponse(response_generator(), media_type='text/plain')


@sites_router.get(
    '/sites/{site_id}',
    summary='Получить сайт',
    response_model=SiteResponse,
)
def get_site(site_id: int, request: Request):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail='Site not found')

    s3_settings = request.app.state.s3_settings
    site_info = SITES[site_id]
    html_url, download_url = build_s3_urls(s3_settings, 'index.html')
    image_url, _ = build_s3_urls(s3_settings, 'index.png')
    return SiteResponse(
        id=site_info['id'],
        title=site_info['title'],
        prompt=site_info['prompt'],
        html_code_url=html_url,
        html_code_download_url=download_url,
        screenshot_url=image_url,
        created_at=site_info['created_at'],
        updated_at=site_info['updated_at'],
    )
