import logging
from itertools import count

from aiobotocore.client import AioBaseClient
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from httpx import AsyncClient

from env_settings import GotenbergSettings, S3Settings

logger = logging.getLogger('uvicorn.error')

SITES: dict[int, dict] = {}
_site_id_counter = count(1)


def generate_site_id() -> int:
    return next(_site_id_counter)


def build_s3_urls(s3_settings: S3Settings, key: str) -> tuple[str, str]:
    base_url = f'{str(s3_settings.endpoint_url)}{s3_settings.bucket_name}/{key}'
    download_url = f'{base_url}?response-content-disposition=attachment'
    return base_url, download_url


async def generate_screenshot(
    gotenberg_client: AsyncClient,
    gotenberg_settings: GotenbergSettings,
    html: str,
    site_id: int,
) -> bytes | None:
    try:
        logger.info(f'[Gotenberg] Генерация скриншота для сайта {site_id}...')
        screenshot_bytes = await ScreenshotHTMLRequest(
            index_html=html,
            width=gotenberg_settings.width,
            format=gotenberg_settings.format,
            wait_delay=gotenberg_settings.wait_delay,
        ).asend(gotenberg_client)
        return screenshot_bytes
    except GotenbergServerError as e:
        logger.error(f'Ошибка Gotenberg: {e}')
    except Exception as e:
        logger.error(f'Ошибка генерации скриншота: {e}')
    return None


async def upload_to_s3(
    s3_client: AioBaseClient,
    s3_settings: S3Settings,
    key: str,
    body: bytes,
    content_type: str,
) -> None:
    try:
        await s3_client.put_object(
            Bucket=s3_settings.bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type,
            ContentDisposition='inline',
        )  # pyright: ignore[reportGeneralTypeIssues]
        logger.info(f'Файл загружен в S3: {s3_settings.bucket_name}/{key}')
    except Exception as e:
        logger.error(f'Ошибка загрузки файла {key} в S3: {e}')


async def publish_site(
    s3_client: AioBaseClient,
    s3_settings: S3Settings,
    gotenberg_client: AsyncClient,
    gotenberg_settings: GotenbergSettings,
    html: str,
    site_id: int,
) -> None:
    await upload_to_s3(
        s3_client=s3_client,
        s3_settings=s3_settings,
        key='index.html',
        body=html.encode('utf-8'),
        content_type='text/html',
    )

    screenshot_bytes = await generate_screenshot(
        gotenberg_client=gotenberg_client,
        gotenberg_settings=gotenberg_settings,
        html=html,
        site_id=site_id,
    )

    if screenshot_bytes:
        await upload_to_s3(
            s3_client=s3_client,
            s3_settings=s3_settings,
            key='index.png',
            body=screenshot_bytes,
            content_type='image/png',
        )
