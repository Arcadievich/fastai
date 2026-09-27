from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

app = FastAPI()


class UserDetailsResponse(BaseModel):
    profileId: int
    email: EmailStr
    username: str = Field(max_length=254)
    registeredAt: datetime
    updatedAt: datetime
    isActive: bool


@app.get(
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


app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
