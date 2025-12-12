from pydantic import BaseModel, EmailStr
from typing import Optional

# ------------ Organization ------------

class OrgCreateRequest(BaseModel):
    organization_name: str
    email: EmailStr
    password: str


class OrgUpdateRequest(BaseModel):
    # old name and new name
    old_organization_name: str
    new_organization_name: str
    # optional admin updates
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class OrgDeleteRequest(BaseModel):
    organization_name: str


class OrgResponse(BaseModel):
    organization_name: str
    collection_name: str
    admin_email: EmailStr


# ------------ Admin & Auth ------------

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
