from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field, PositiveInt
from pydantic.alias_generators import to_camel


class UserDetailsResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    profile_id: PositiveInt
    email: EmailStr
    username: str = Field(max_length=254)
    registered_at: datetime
    updated_at: datetime
    is_active: bool


class CreateSiteRequest(BaseModel):
    title: str | None = Field(default=None, max_length=128)
    prompt: str


class SiteGenerationRequest(BaseModel):
    prompt: str


class SiteResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    id: PositiveInt
    title: str
    html_code_url: AnyHttpUrl | None = None
    html_code_download_url: AnyHttpUrl | None = None
    screenshot_url: AnyHttpUrl | None = None
    prompt: str
    created_at: datetime
    updated_at: datetime


class GeneratedSitesResponse(BaseModel):
    sites: list[SiteResponse]
