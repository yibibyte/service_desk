from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    login: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    role: str
    full_name: str


class UserIn(BaseModel):
    login: str
    password: str
    full_name: str
    email: EmailStr
    phone: str
    role: str


class UserOut(BaseModel):
    id: int
    login: str
    full_name: str
    email: str
    phone: str
    role: str

    class Config:
        from_attributes = True


class EquipmentIn(BaseModel):
    inventory_number: str
    name: str
    model: Optional[str] = None
    location: Optional[str] = None
    status: str = 'в работе'
    commissioning_date: date
    work_start_date: Optional[date] = None
    decommission_date: Optional[date] = None


class EquipmentOut(EquipmentIn):
    id: int

    class Config:
        from_attributes = True


class RequestIn(BaseModel):
    equipment_id: int
    description: str
    priority: str = 'средний'
    planned_start: date
    planned_end: date
    assignee_id: Optional[int] = None


class RequestOut(BaseModel):
    id: int
    request_number: str
    equipment_id: int
    author_id: int
    assignee_id: Optional[int]
    description: str
    priority: str
    status: str
    created_date: date
    planned_start: date
    planned_end: date
    actual_start: Optional[date]
    actual_end: Optional[date]

    class Config:
        from_attributes = True


class StatusIn(BaseModel):
    status: str


class MaterialIn(BaseModel):
    name: str
    unit: str = 'шт.'
    price: float = 0
    stock_qty: float = 0


class MaterialOut(MaterialIn):
    id: int

    class Config:
        from_attributes = True


class RequestMaterialIn(BaseModel):
    material_id: int
    qty: float


class MaintenanceIn(BaseModel):
    equipment_id: int
    planned_date: date
    description: str


class MaintenanceOut(MaintenanceIn):
    id: int
    performed: bool
    performed_date: Optional[date]
    performer_id: Optional[int]

    class Config:
        from_attributes = True
