from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas, security
from .db import get_db

auth_router = APIRouter(prefix='/api/auth', tags=['auth'])
equipment_router = APIRouter(prefix='/api/equipment', tags=['equipment'])
requests_router = APIRouter(prefix='/api/requests', tags=['requests'])
materials_router = APIRouter(prefix='/api/materials', tags=['materials'])
maintenance_router = APIRouter(prefix='/api/maintenance', tags=['maintenance'])
users_router = APIRouter(prefix='/api/users', tags=['users'])
reports_router = APIRouter(prefix='/api/reports', tags=['reports'])

ALL_ROUTERS = [auth_router, equipment_router, requests_router,
               materials_router, maintenance_router, users_router, reports_router]


# --------------------------- Аутентификация ---------------------------

@auth_router.post('/login', response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.login == data.login).first()
    if not user or user.password_hash != security.hash_password(data.password):
        raise HTTPException(401, 'Неверный логин или пароль')
    return {
        'access_token': security.create_token(user.id, user.role),
        'role': user.role,
        'full_name': user.full_name,
    }


# ------------------------------ Оборудование ------------------------------

@equipment_router.get('/', response_model=list[schemas.EquipmentOut])
def list_equipment(status: str | None = None, search: str | None = None,
                   db: Session = Depends(get_db),
                   user: models.User = Depends(security.get_current_user)):
    q = db.query(models.Equipment)
    if status:
        q = q.filter(models.Equipment.status == status)
    if search:
        q = q.filter(models.Equipment.name.ilike(f'%{search}%'))
    return q.order_by(models.Equipment.id).all()


@equipment_router.post('/', response_model=schemas.EquipmentOut, status_code=201)
def create_equipment(data: schemas.EquipmentIn, db: Session = Depends(get_db),
                     user: models.User = Depends(security.require_role('администратор', 'мастер'))):
    item = models.Equipment(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@equipment_router.put('/{item_id}', response_model=schemas.EquipmentOut)
def update_equipment(item_id: int, data: schemas.EquipmentIn,
                     db: Session = Depends(get_db),
                     user: models.User = Depends(security.require_role('администратор', 'мастер'))):
    item = db.get(models.Equipment, item_id)
    if not item:
        raise HTTPException(404, 'Оборудование не найдено')
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@equipment_router.delete('/{item_id}', status_code=204)
def delete_equipment(item_id: int, db: Session = Depends(get_db),
                     user: models.User = Depends(security.require_role('администратор'))):
    item = db.get(models.Equipment, item_id)
    if not item:
        raise HTTPException(404, 'Оборудование не найдено')
    db.delete(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # СУБД блокирует удаление по RESTRICT, если есть связанные заявки/ТО
        raise HTTPException(409, 'Нельзя удалить: есть связанные заявки или график ТО')


# -------------------------------- Заявки ---------------------------------

def _next_request_number(db: Session) -> str:
    year = date.today().year
    count = db.query(func.count(models.ServiceRequest.id)).scalar() or 0
    return f'Z-{year}-{count + 1:04d}'


@requests_router.get('/', response_model=list[schemas.RequestOut])
def list_requests(status: str | None = None, priority: str | None = None,
                  db: Session = Depends(get_db),
                  user: models.User = Depends(security.get_current_user)):
    q = db.query(models.ServiceRequest)
    if status:
        q = q.filter(models.ServiceRequest.status == status)
    if priority:
        q = q.filter(models.ServiceRequest.priority == priority)
    return q.order_by(models.ServiceRequest.id.desc()).all()


@requests_router.post('/', response_model=schemas.RequestOut, status_code=201)
def create_request(data: schemas.RequestIn, db: Session = Depends(get_db),
                   user: models.User = Depends(security.get_current_user)):
    if data.planned_start >= data.planned_end:
        raise HTTPException(422, 'Плановое окончание должно быть позже планового начала')
    req = models.ServiceRequest(
        request_number=_next_request_number(db),
        author_id=user.id,
        **data.model_dump(),
    )
    if req.assignee_id:
        req.status = 'назначена'
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@requests_router.patch('/{req_id}/status', response_model=schemas.RequestOut)
def change_status(req_id: int, data: schemas.StatusIn,
                  db: Session = Depends(get_db),
                  user: models.User = Depends(security.get_current_user)):
    if data.status not in models.REQUEST_STATUSES:
        raise HTTPException(422, 'Недопустимый статус')
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, 'Заявка не найдена')
    req.status = data.status
    if data.status == 'в работе' and req.actual_start is None:
        req.actual_start = date.today()
    if data.status in ('выполнена', 'закрыта') and req.actual_end is None:
        req.actual_end = date.today()
    db.commit()
    db.refresh(req)
    return req


@requests_router.delete('/{req_id}', status_code=204)
def delete_request(req_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(security.require_role('администратор'))):
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, 'Заявка не найдена')
    db.delete(req)  # материалы заявки удаляются каскадом (CASCADE)
    db.commit()


@requests_router.get('/{req_id}/materials')
def list_request_materials(req_id: int, db: Session = Depends(get_db),
                           user: models.User = Depends(security.get_current_user)):
    rows = db.query(models.RequestMaterial).filter_by(request_id=req_id).all()
    return [{'id': r.id, 'material_id': r.material_id, 'name': r.material.name,
             'qty': float(r.qty), 'price': float(r.material.price),
             'sum': float(r.qty) * float(r.material.price)} for r in rows]


@requests_router.post('/{req_id}/materials', status_code=201)
def add_request_material(req_id: int, data: schemas.RequestMaterialIn,
                         db: Session = Depends(get_db),
                         user: models.User = Depends(security.get_current_user)):
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, 'Заявка не найдена')
    material = db.get(models.Material, data.material_id)
    if not material:
        raise HTTPException(404, 'Материал не найден')
    if float(material.stock_qty) < data.qty:
        raise HTTPException(422, 'Недостаточно материала на складе')
    material.stock_qty = float(material.stock_qty) - data.qty
    if req.status in ('создана', 'назначена', 'в работе'):
        req.status = 'ожидает материалов' if req.status != 'в работе' else 'в работе'
    row = models.RequestMaterial(request_id=req_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {'detail': 'Материал списан'}


# -------------------------------- Материалы --------------------------------

@materials_router.get('/', response_model=list[schemas.MaterialOut])
def list_materials(db: Session = Depends(get_db),
                   user: models.User = Depends(security.get_current_user)):
    return db.query(models.Material).order_by(models.Material.name).all()


@materials_router.post('/', response_model=schemas.MaterialOut, status_code=201)
def create_material(data: schemas.MaterialIn, db: Session = Depends(get_db),
                    user: models.User = Depends(security.require_role('администратор'))):
    item = models.Material(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ------------------------------ График ТО ------------------------------

@maintenance_router.get('/', response_model=list[schemas.MaintenanceOut])
def list_maintenance(equipment_id: int | None = None,
                     only_pending: bool = False,
                     db: Session = Depends(get_db),
                     user: models.User = Depends(security.get_current_user)):
    q = db.query(models.Maintenance)
    if equipment_id:
        q = q.filter(models.Maintenance.equipment_id == equipment_id)
    if only_pending:
        q = q.filter(models.Maintenance.performed.is_(False))
    return q.order_by(models.Maintenance.planned_date).all()


@maintenance_router.post('/', response_model=schemas.MaintenanceOut, status_code=201)
def create_maintenance(data: schemas.MaintenanceIn, db: Session = Depends(get_db),
                       user: models.User = Depends(security.require_role('администратор', 'мастер'))):
    if not db.get(models.Equipment, data.equipment_id):
        raise HTTPException(404, 'Оборудование не найдено')
    item = models.Maintenance(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@maintenance_router.post('/{item_id}/complete', response_model=schemas.MaintenanceOut)
def complete_maintenance(item_id: int, db: Session = Depends(get_db),
                         user: models.User = Depends(security.require_role('администратор', 'мастер'))):
    item = db.get(models.Maintenance, item_id)
    if not item:
        raise HTTPException(404, 'Запись ТО не найдена')
    item.performed = True
    item.performed_date = date.today()
    item.performer_id = user.id
    db.commit()
    db.refresh(item)
    return item


# -------------------------------- Пользователи --------------------------------

@users_router.get('/', response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db),
               user: models.User = Depends(security.require_role('администратор'))):
    return db.query(models.User).order_by(models.User.id).all()


@users_router.post('/', response_model=schemas.UserOut, status_code=201)
def create_user(data: schemas.UserIn, db: Session = Depends(get_db),
                user: models.User = Depends(security.require_role('администратор'))):
    if data.role not in models.ROLES:
        raise HTTPException(422, 'Недопустимая роль')
    new_user = models.User(**data.model_dump(exclude={'password'}),
                           password_hash=security.hash_password(data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# -------------------------------- Отчеты --------------------------------

@reports_router.get('/summary')
def summary(db: Session = Depends(get_db),
            user: models.User = Depends(security.get_current_user)):
    by_status = dict(db.query(models.ServiceRequest.status,
                              func.count(models.ServiceRequest.id))
                     .group_by(models.ServiceRequest.status).all())
    total_equipment = db.query(func.count(models.Equipment.id)).scalar() or 0
    in_repair = db.query(func.count(models.Equipment.id)) \
        .filter(models.Equipment.status == 'в ремонте').scalar() or 0
    pending_to = db.query(func.count(models.Maintenance.id)) \
        .filter(models.Maintenance.performed.is_(False)).scalar() or 0
    consumption = db.query(models.Material.name,
                           func.sum(models.RequestMaterial.qty)) \
        .join(models.RequestMaterial,
              models.RequestMaterial.material_id == models.Material.id) \
        .group_by(models.Material.name).all()
    return {
        'requests_by_status': by_status,
        'total_equipment': total_equipment,
        'equipment_in_repair': in_repair,
        'pending_maintenance': pending_to,
        'materials_consumption': {name: float(qty) for name, qty in consumption},
    }
