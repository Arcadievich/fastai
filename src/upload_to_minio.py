import asyncio
import logging
import mimetypes
from pathlib import Path

import aioboto3
from aiobotocore.config import AioConfig

from env_settings import app_settigns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCAL_FILE_PATH = 'C:/Users/Admin/Desktop/dvmn_homework/fastai-1/chapman.html'
BUCKET_NAME = 'dvmnhomework'
S3_KEY = Path(LOCAL_FILE_PATH).name


async def upload_file_to_s3():
    config = AioConfig(
        max_pool_connections=10,
        connect_timeout=10,
        read_timeout=10,
    )

    session = aioboto3.Session()

    content_type, _ = mimetypes.guess_type(LOCAL_FILE_PATH)
    if not content_type:
        content_type = 'application/octet-stream'

    try:
        with open(LOCAL_FILE_PATH, 'rb') as file:
            file_data = file.read()

        async with session.client(
            's3',
            endpoint_url='http://127.0.0.1:9000',
            aws_access_key_id=app_settigns.s3.access_key.get_secret_value(),
            aws_secret_access_key=app_settigns.s3.secret_key.get_secret_value(),
            config=config,
            region_name='us-east-1',
        ) as s3_client:  # pyright: ignore[reportGeneralTypeIssues]

            logger.info(f'Начинаю загрузку {LOCAL_FILE_PATH} в бакет {BUCKET_NAME}...')

            await s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=S3_KEY,
                Body=file_data,
                ContentType=content_type,
                ContentDisposition='inline',
            )

            logger.info('Файл успешно загружен!')
            logger.info(f'Ссылка для просмотра: http://127.0.0.1:9000/{BUCKET_NAME}/{S3_KEY}')

    except Exception as e:
        logger.error(f'Ошибка при загрузке файла: {e}')
        raise


if __name__ == '__main__':
    asyncio.run(upload_file_to_s3())
