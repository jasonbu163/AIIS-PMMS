from common.schema_base import ApiSchema


class LoginIn(ApiSchema):
    username: str
    password: str


class LogoutIn(ApiSchema):
    refresh_token: str


class RefreshIn(ApiSchema):
    refresh_token: str


class TokenOut(ApiSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(ApiSchema):
    username: str
    display_name: str
    role: str
    status: str
