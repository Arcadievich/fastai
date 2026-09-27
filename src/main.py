from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()


@app.get('/users/me', summary='Получить учетные данные пользователя')
def mock_get_user():
    mock_user_info = {
        'email': 'user_274@mail.ru',
        'isActive': True,
        'profileId': '1',
        'registeredAt': '2025-06-15T18:29:56+00:00',
        'updatedAt': '2025-06-15T18:29:56+00:00',
        'username': 'arcadievich',
    }

    return JSONResponse(content=mock_user_info, status_code=200)


app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
