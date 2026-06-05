from __future__ import annotations

from typing import Literal, Optional

from common.schema_base import ApiSchema

UserRole = Literal["admin", "operator", "viewer"]
UserStatus = Literal["active", "disabled"]


class UserCreateIn(ApiSchema):
    username: str
    password: str
    display_name: str
    role: UserRole = "viewer"
    status: UserStatus = "active"


class UserUpdateIn(ApiSchema):
    display_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserPasswordUpdateIn(ApiSchema):
    new_password: str
    old_password: Optional[str] = None


class UserOut(ApiSchema):
    username: str
    display_name: str
    role: str
    status: str
