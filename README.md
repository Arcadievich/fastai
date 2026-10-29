# FastAI

Данный проект содержит генератор сайтов, комбинирующий в себе использование нескольких нейросетей, которые заранее настроены на комплексную обработку запросов, что позволяет получить рабочую html-страницу с первого раза.

## Установка

- Установите [Python](https://www.python.org/downloads/) на свой ПК
- Склонируйте данный [репозиторий](https://github.com/Arcadievich/fastai/archive/refs/heads/main.zip) на свой ПК
- Установите пакетный менеджер `uv`:

Команда для Linux:
```bash
sudo snap install astral-uv --classic
```
или
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Команда для Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

- Установите зависимости и создайте виртуальную среду Python, используя следующую команду внутри папки с репозиторием:

```bash
uv sync
```

### Установка S3 MinIO

- Установите язык GO в вашу систему с официального сайта. [Установщик для Windows](https://dl.google.com/go/go1.27.3.windows-amd64.msi). Откройте терминал и проверьте установку командой:

```bash
go version
```

- Затем необходимо с помощью Go скомпилировать и установить MinIO из github репозитория командой:

```bash
go install github.com/minio/minio@latest
```

Эта команда загрузит исходный код, скомпилирует его и поместит `minio.exe` в каталог `bin` вашего `GOPATH` (обычно `C:\Users\ваше_имя\go\bin`).

- Создайте сервер. Сначала создайте пустую папку для хранения данных, например `D:\minio-data`. Затем выполните:

```bash
C:\Users\ваше_имя\go\bin\minio.exe server D:\minio-data --console-address ":9001"
```

- Войдите в систему. После успешного запуска откройте в браузере `http://127.0.0.1:9001` и войдите, используя имя пользователя и пароль по умолчанию `minioadmin` / `minioadmin`.

- Создайте бакет используя интерфейс MinIO в браузере

- Измените приватность созданного бакета:
    - Скачайте `mc` (minio client) с github. [mc.exe для Windows](https://github.com/minio/mc/releases/download/RELEASE.2025-08-13T08-35-41Z/mc.windows-amd64.RELEASE.2025-08-13T08-35-41Z.exe), [список всех версий](https://github.com/minio/mc/releases/)
    - Измените название файла на `mc.exe` и сохраните его в папку, например `C:\minio`
    - Настройте alias. Откройте `PowerShell` в папке с `mc.exe` и выполните следующую команду, чтобы сообщить `mc` адрес вашего сервера и учетные данные:

```bash
.\mc.exe alias set mylocal http://127.0.0.1:9000 minioadmin minioadmin
```

Установите публичный доступ к бакету следующей командой:

```bash
.\mc.exe anonymous set download mylocal/<backet_name>
```

Важно! В коде для загрузки файлов в бакет S3, в методе `put_object` необходимо указывать параметр `ContentDisposition` со значением `inline`, а также правильные MIME-типы в параметре `ContentType`

Вручную положите файл `index.html` в бакет через [веб-интерфейс](http://127.0.0.1:9001)

### Настройка переменных окружения

В корневой папке репозитория создайте `.env` файл, вставьте в него содержимое `example.env` файла и вставьте реальные значения переменных. Ниже указан перечень переменных и способы их получения. Обязательные для заполнения отмечены восклицательным знаком.

#### DEBUG и VSEGPT

- `DEBUG` - режим работы приложения, по умолчанию `True` (разработка)
- ❗️`VSEGPT__API_TOKEN` - [VseGPT](https://vsegpt.ru/Docs/Models#h46-6) позволяет произвести оплату с карт РФ. [Регистрация и настройка](https:/gist.    github.com/DevmanServices/f890a4efbab6bf5690809ded7404e82e)
- `VSEGPT__URL` - URL нейросети (по умолчанию - `https://api.vsegpt.ru/v1`)
- ❗️`VSEGPT__MODEL` - Если используете сервис как замену стандартного DeepSeek, то используйте `deepseek/deepseek-chat` как аналог официальной   `deepseek-chat`
- `VSEGPT__MAX_CONNECTIONS` - Максимальное количество одновременных подключений

#### Unsplash

- ❗️`UNSPLASH__API_TOKEN` - Токен Unsplash. Зарегистрируйте аккаунт по [ссылке](https://unsplash.com/documentation#creating-a-developer-account),создайте    [demo-приложение](https://unsplash.com/oauth/applications), скопируйте токен доступа(Access Key), как на [скриншоте](https://dvmn.orgmedia/filer_public/  de/2f/de2fe81a-6823-4d85-a9a5-0033675fd39a/screenshot.png)
- `UNSPLASH__MAX_CONNECTIONS` - Максимальное количество одновременных подключений
- `UNSPLASH__TIMEOUT` - Время ожидания подключения к Unsplash

#### S3

- `S3__ENDPOINT_URL` - Локальный адрес MinIO, запущенного на вашем компьютере
- ❗️`S3__ACCESS_KEY` - Ваше имя пользователя в MinIO
- ❗️`S3__SECRET_KEY` - Ваш пароль в MinIO
- ❗️`S3__BUCKET_NAME` - Название вашего бакета в MinIO
- `S3__CONNECT_TIMEOUT` - Время ожидания подключения к MinIO
- `S3__READ_TIMEOUT` - Время ожидания чтения файла из бакета
- `S3__MAX_CONNECTIONS` - Максимальное количество одновременных подключений

#### Gotenberg

- `GOTENBERG__API_URL` - Базовый url Gotenberg API
- `GOTENBERG__WIDTH` - Ширина генерируемого скриншота
- `GOTENBERG__FORMAT` - Формат файла скриншота
- `GOTENBERG__MAX_CONNECTIONS` - Максимальное количество одновременных подключений
- `GOTENBERG__TIMEOUT` - Время ожидания подключения к Gotenberg
- `GOTENBERG__WAIT_DELAY` - Время ожидания завершения анимаций на html-странице. Важно: время ожидания завершения анимаций должно быть меньшетаймаута  асинхронного клиента, иначе библиотека всегда будет возвращать `TimeoutError`.

Убедитесь, что `.env` файл добавлен в `.gitignore`!

## Запуск

- Откройте командную строку и запустите MinIO (если ещё не запущен) командой (для Windows):

```bash
C:\Users\ваше_имя\go\bin\minio.exe server D:\minio-data --console-address ":9001"
```

- Для запуска сайта запустите ещё одну командную строку и перейдите в папку с репозиторием
- Запустите виртуальное окружение Python:

Команда для Windows:
```bash
.venv\Scripts\activate
```

Команда для Linux:
```bash
source ./venv/Scripts/activate
```

- Запустите сайт командой:

```bash
fastapi dev src/main.py
```

Пример успешного запуска в командной строке:

<img width="1260" height="972" alt="fastai-example-1" src="https://github.com/user-attachments/assets/7735a0a2-9247-4b58-a123-50f5cf9e7833" />

Пример успешного запуска в [браузере](http://127.0.0.1:8000):

<img width="1915" height="986" alt="fastai-example-2" src="https://github.com/user-attachments/assets/75dff137-fc32-44c6-bb1c-a16b4577ee77" />

## Репозиторий для бэкенд-разработчиков.

Инструкции и справочная информация по разворачиванию локальной инсталляции собраны
в документе [CONTRIBUTING.md](./CONTRIBUTING.md).

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org).
