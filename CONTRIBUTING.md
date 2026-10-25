# Разработчикам бэкенда

[TOC]

## Как развернуть локально

### Необходимое ПО

Для запуска ПО вам понадобятся консольный Git и Make. Инструкции по их установке ищите на
официальных сайтах:

- [Git SCM](https://git-scm.com/)
- [GNU Make](https://www.gnu.org/software/make/)

Вы можете проверить, установлены ли эти программы с помощью команд:
```shell
$ git --version
git version 2.37.1.windows.1

$ make --version
GNU Make 4.4.1
Built for Windows32
<...>
```

Для тех, кто использует Windows необходимы также программы **git** и **git bash**. В **git bash** необходимо дополнительно установить
**make**:

- Перейдите на сайт [ezwinports](https://sourceforge.net/projects/ezwinports/files/)
- Скачайте `make-4.4.1-without-guile-w32-bin.zip` (выберите версию без `guile`)
- Извлеките архив
- Скопируйте содержимое архива в `C:\ProgramFiles\Git\mingw64\` **БЕЗ** перезаписи/замены любых вложенных файлов.

Все дальнейшие команды запускать из-под **git bash**.

### Создание виртуального окружения для работы с IDE

IDE для корректной работы подсказок необходимо развернуть виртуальное окружение со всеми установленными зависимостями.

В качестве пакетного менеджера на проекта используется [uv](https://docs.astral.sh/uv/).

[Установите uv](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/Uv-package-manager#1-%D1%83%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-uv) и в корне репозитория выполните команду

```shell
$ uv sync
```

[uv](https://docs.astral.sh/uv/) создаст виртуальное окружение, установит необходимую версию Python и все необходимые зависимости.

После этого активируйте виртуальное окружение в текущей сессии терминала:

```shell
$ source .venv/bin/activate  # для Linux
$ .\.venv\Scripts\activate  # Для Windows
```

### Настройка pre-commit хуков

В репозитории используются хуки [pre-commit](https://pre-commit.com/), чтобы автоматически запускать линтеры и автотесты.

В корне репозитория в **активированном виртуальном окружении** запустите команду для настройки хуков:

```shell
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

В последующем при коммите автоматически будут запускаться линтеры и другие проверки. Если проверки не пройдут, то коммит прервётся с ошибкой.

Если вам потребуется сделать коммит без проверок, то вы можете отключить их с помощью флага `--no-verify`:
```shell
git commit -m 'Message' --no-verify
```

### Установка и запуск MinIO

- Установите язык GO в вашу систему с официального сайта. (Установщик для Windows)[https://dl.google.com/go/go1.27.3.windows-amd64.msi]. Откройте терминал и проверьте установку командой:

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
    - Скачайте `mc` (minio client) с github. (mc.exe для Windows)[https://github.com/minio/mc/releases/download/RELEASE.2025-08-13T08-35-41Z/mc.windows-amd64.RELEASE.2025-08-13T08-35-41Z.exe], (список всех версий)[https://github.com/minio/mc/releases/]
    - Измените название файла на `mc.exe` и сохраните его в папку, например `C:\minio`
    - Настройте alias. Откройте `PowerShell` в папке с `mc.exe` и выполните следующую команду, чтобы сообщить `mc` адрес вашего сервера и учетные данные:

```bash
.\mc.exe alias set mylocal http://127.0.0.1:9000 minioadmin minioadmin
```

Установите публичный доступ к бакету следующей командой:

```bash
.\mc.exe anonymous set download mylocal/<backet_name>
```

Вручную положите файл `index.html` в бакет через (веб-интерфейс)[http://127.0.0.1:9001]

### Настройка переменных окружения

Внутри репозитория создайте файл `.env`, скопируйте в него переменные из файла `example.env` и подставьте реальные значения.

Убедитесь, что `.env` файл добавлен в `.gitignore`!

Перечень переменных и способы их получения:
- `DEBUG` - режим работы приложения, по умолчанию `True` (разработка)
- `VSEGPT__API_TOKEN` - [VseGPT](https://vsegpt.ru/Docs/Models#h46-6) позволяет произвести оплату с карт РФ. (Регистрация и настройка)[https://gist.github.com/DevmanServices/f890a4efbab6bf5690809ded7404e82e]
- `VSEGPT__URL` - URL нейросети (по умолчанию - `https://api.vsegpt.ru/v1`)
- `VSEGPT__MODEL` - Если используете сервис как замену стандартного DeepSeek, то используйте `deepseek/deepseek-chat` как аналог официальной `deepseek-chat`
- `VSEGPT__MAX_CONNECTIONS` - Максимальное количество одновременных подключений
- `UNSPLASH__API_TOKEN` - Токен Unsplash. Зарегистрируйте аккаунт по (ссылке)[https://unsplash.com/documentation#creating-a-developer-account], создайте (demo-приложение)[https://unsplash.com/oauth/applications], скопируйте токен доступа(Access Key), как на (скриншоте)[https://dvmn.org/media/filer_public/de/2f/de2fe81a-6823-4d85-a9a5-0033675fd39a/screenshot.png]
- `UNSPLASH__MAX_CONNECTIONS` - Максимальное количество одновременных подключений
- `UNSPLASH__TIMEOUT` - Время ожидания подключения к Unsplash
- `S3__ENDPOINT_URL` - Локальный адрес MinIO, запущенного на вашем компьютере
- `S3__ACCESS_KEY` - Ваше имя пользователя в MinIO
- `S3__SECRET_KEY` - Ваш пароль в MinIO
- `S3__BUCKET_NAME` - Название вашего бакета в MinIO
- `S3__CONNECT_TIMEOUT` - Время ожидания подключения к MinIO
- `S3__READ_TIMEOUT` - Время ожидания чтения файла из бакета
- `S3__MAX_CONNECTIONS` - Максимальное количество одновременных подключений

## Как вести разработку

Код проекта находится в папке `/src`.

Находясь в корневой директории проекта, запустить проект можно командой:

```shell
$ fastapi dev src/main.py
```

Проект будет работать по адресу http://127.0.0.1:8000/

### Как установить python-пакет в виртуальное окружение

В качестве менеджера пакетов используется [uv](https://docs.astral.sh/uv/).

Вот пример как добавить в зависимости библиотеку `beautifulsoup4`.

```shell
$ uv add beautifulsoup4
```

Конфигурационные файлы `pyproject.toml` и `uv.lock` обновятся автоматически.

Аналогичным образом можно удалять python-пакеты:

```shell
$ uv remove beautifulsoup4
```

Если необходимо обновить `uv.lock` вручную, то используйте команду:

```shell
$ uv lock
```

### Команды для быстрого запуска с помощью make

Для вывода списка часто используемых коротких команд используйте команду

```shell
$ make list
...
```

### Схемы приложения

- [Локальная инсталляция бэкенда](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/fastai/backend_local_installation.drawio.png)
- [Prod инсталляция бэкенда](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/fastai/backend_prod_installation.drawio.png)
- [Декомпозиция бэкенда по подсистемам](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/fastai/backend_decomposition.drawio.png)

### Как подключить фронтенд к локальной инсталяции

- Скачайте архив с [фронтендом](https://dvmn.org/filer/canonical/1750917110/1035/)
- Папку `frontend` из архива положите в корень проекта
- В папке `frontend` создайте файл `frontend-settings.json`, в котором укажите `backendBaseUrl`:

```json
{"backendBaseUrl": "localhost:8000"}
```

- В файле `src/main.py` подключите статику из папки frontend:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
```

- Более подробную инструкцию можно открыть по [ссылке](https://dvmn.org/media/filer_public/a6/72/a6723390-983e-48df-b1ac-e2785682c671/readme.html)
