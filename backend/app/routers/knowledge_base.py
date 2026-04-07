import json
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.knowledge_base import KnowledgeBase, KBField, KBRecord

router = APIRouter(prefix="/kb", tags=["База знаний"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class KBCreate(BaseModel):
    name: str

class KBRename(BaseModel):
    name: str

class FieldCreate(BaseModel):
    name: str
    field_type: str = "text"

class FieldUpdate(BaseModel):
    name: Optional[str] = None
    field_type: Optional[str] = None

class RecordCreate(BaseModel):
    data: dict = {}

class RecordUpdate(BaseModel):
    data: dict  # partial: {field_name: new_value}


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_kb(kb_id: str, user: User, db: AsyncSession) -> KnowledgeBase:
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == user.id)
        .options(selectinload(KnowledgeBase.fields), selectinload(KnowledgeBase.records))
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="База не найдена")
    return kb


def _kb_to_dict(kb: KnowledgeBase) -> dict:
    return {
        "id": kb.id,
        "name": kb.name,
        "created_at": kb.created_at,
        "fields": [{"id": f.id, "name": f.name, "field_type": f.field_type, "sort_order": f.sort_order} for f in kb.fields],
        "records": [{"id": r.id, "data": json.loads(r.data), "created_at": r.created_at} for r in kb.records],
    }


# ─── Эндпоинты ────────────────────────────────────────────────────────────────

@router.get("")
async def list_kbs(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == user.id)
        .options(selectinload(KnowledgeBase.fields))
        .order_by(KnowledgeBase.created_at.desc())
    )
    kbs = result.scalars().all()
    return [{"id": k.id, "name": k.name, "created_at": k.created_at, "fields_count": len(k.fields)} for k in kbs]


@router.post("", status_code=201)
async def create_kb(data: KBCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kb = KnowledgeBase(user_id=user.id, name=data.name)
    db.add(kb)
    await db.flush()
    return {"id": kb.id, "name": kb.name, "fields_count": 0}


@router.get("/{kb_id}/webhook-token")
async def get_kb_webhook_token(kb_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Получить токен для внешнего вебхука базы знаний."""
    import hashlib
    from ..core.config import settings
    await _get_kb(kb_id, user, db)  # проверка доступа
    token = hashlib.sha256(f"kb:{kb_id}:{settings.SECRET_KEY}".encode()).hexdigest()[:32]
    return {"kb_id": kb_id, "token": token}


@router.get("/{kb_id}")
async def get_kb(kb_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kb = await _get_kb(kb_id, user, db)
    return _kb_to_dict(kb)


@router.patch("/{kb_id}")
async def rename_kb(kb_id: str, data: KBRename, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kb = await _get_kb(kb_id, user, db)
    kb.name = data.name
    await db.flush()
    return {"id": kb.id, "name": kb.name}


@router.delete("/{kb_id}", status_code=204)
async def delete_kb(kb_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kb = await _get_kb(kb_id, user, db)
    await db.delete(kb)


# ─── Поля (колонки) ───────────────────────────────────────────────────────────

@router.post("/{kb_id}/fields", status_code=201)
async def add_field(kb_id: str, data: FieldCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kb = await _get_kb(kb_id, user, db)
    sort_order = len(kb.fields)
    field = KBField(kb_id=kb_id, name=data.name, field_type=data.field_type, sort_order=sort_order)
    db.add(field)
    await db.flush()
    return {"id": field.id, "name": field.name, "field_type": field.field_type, "sort_order": field.sort_order}


@router.patch("/{kb_id}/fields/{field_id}")
async def update_field(kb_id: str, field_id: str, data: FieldUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _get_kb(kb_id, user, db)
    result = await db.execute(select(KBField).where(KBField.id == field_id, KBField.kb_id == kb_id))
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Поле не найдено")
    if data.name is not None:
        field.name = data.name
    if data.field_type is not None:
        field.field_type = data.field_type
    await db.flush()
    return {"id": field.id, "name": field.name, "field_type": field.field_type}


@router.delete("/{kb_id}/fields/{field_id}", status_code=204)
async def delete_field(kb_id: str, field_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _get_kb(kb_id, user, db)
    result = await db.execute(select(KBField).where(KBField.id == field_id, KBField.kb_id == kb_id))
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Поле не найдено")
    await db.delete(field)


# ─── Записи (строки) ──────────────────────────────────────────────────────────

@router.post("/{kb_id}/records", status_code=201)
async def add_record(kb_id: str, data: RecordCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _get_kb(kb_id, user, db)
    record = KBRecord(kb_id=kb_id, data=json.dumps(data.data, ensure_ascii=False))
    db.add(record)
    await db.flush()
    return {"id": record.id, "data": data.data, "created_at": record.created_at}


@router.patch("/{kb_id}/records/{record_id}")
async def update_record(kb_id: str, record_id: str, data: RecordUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _get_kb(kb_id, user, db)
    result = await db.execute(select(KBRecord).where(KBRecord.id == record_id, KBRecord.kb_id == kb_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    current = json.loads(record.data)
    current.update(data.data)
    record.data = json.dumps(current, ensure_ascii=False)
    await db.flush()
    return {"id": record.id, "data": current}


@router.delete("/{kb_id}/records/{record_id}", status_code=204)
async def delete_record(kb_id: str, record_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _get_kb(kb_id, user, db)
    result = await db.execute(select(KBRecord).where(KBRecord.id == record_id, KBRecord.kb_id == kb_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    await db.delete(record)


# ─── Импорт / Экспорт CSV ─────────────────────────────────────────────────────

@router.post("/{kb_id}/import")
async def import_csv(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = await _get_kb(kb_id, user, db)
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except Exception:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    headers = list(reader.fieldnames or [])
    if not headers:
        raise HTTPException(status_code=400, detail="Пустой или некорректный CSV")

    # Добавляем новые колонки
    existing = {f.name for f in kb.fields}
    for i, h in enumerate(headers):
        if h and h not in existing:
            db.add(KBField(kb_id=kb_id, name=h, field_type="text", sort_order=len(existing) + i))

    # Создаём записи
    rows = list(reader)
    for row in rows:
        data = {k: v for k, v in row.items() if k}
        db.add(KBRecord(kb_id=kb_id, data=json.dumps(data, ensure_ascii=False)))

    await db.flush()
    return {"imported": len(rows), "columns": len(headers)}


@router.get("/{kb_id}/export")
async def export_csv(kb_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kb = await _get_kb(kb_id, user, db)
    field_names = [f.name for f in kb.fields]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(field_names)
    for rec in kb.records:
        data = json.loads(rec.data)
        writer.writerow([data.get(f, "") for f in field_names])

    filename = kb.name.replace('"', '') + ".csv"
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
