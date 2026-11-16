from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRole(str, Enum):
    """The roles a user can have."""

    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """A registered person who can own content."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    email: EmailStr
    hashed_password: str = Field(min_length=1)
    role: UserRole = UserRole.USER

    @model_validator(mode="after")
    def lowercase_email(self) -> "User":
        """Store the email lowercase so differently-cased emails are one account."""
        self.email = self.email.lower()
        return self
