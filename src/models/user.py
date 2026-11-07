from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    email: EmailStr
    hashed_password: str = Field(min_length=1)
    role: UserRole = UserRole.USER

    @model_validator(mode="after")
    def lowercase_email(self):
        self.email = self.email.lower()
        return self
