from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    requires_2fa: Optional[bool] = False


class TwoFactorCode(BaseModel):
    code: str


class Enable2FARequest(BaseModel):
    code: str
    secret: str


class TOTPSecret(BaseModel):
    secret: str
    qr_url: str


class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None


class TransactionOut(BaseModel):
    id: int
    amount: float
    category: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
