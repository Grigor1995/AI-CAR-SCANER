"""Shared native-client profiles and privacy-preserving reports."""
from io import BytesIO
from pathlib import Path
from threading import RLock
from uuid import uuid4
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from api.state import sessions
from diagnostic.models import Vehicle
from diagnostic.session_persistence import SessionStateBase, persistence

router = APIRouter(prefix='/api/v1', tags=['native-client-features'])


class VehicleProfileRow(SessionStateBase):
    __tablename__ = 'vehicle_profiles'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class ProfileRequest(BaseModel):
    name: str = Field(default='', max_length=200)
    vehicle: Vehicle


_profile_cache: dict[str, dict] = {}
_lock = RLock()


def _engine():
    engine = persistence.engine if persistence.enabled else None
    if engine is not None:
        VehicleProfileRow.__table__.create(engine, checkfirst=True)
    return engine


@router.get('/vehicle-profiles')
def list_profiles():
    with _lock:
        engine = _engine()
        if engine is None:
            return list(_profile_cache.values())
        with Session(engine) as db:
            return [dict(row.payload, id=row.id) for row in db.scalars(select(VehicleProfileRow))]


def _save_profile(profile_id: str, request: ProfileRequest, create: bool):
    payload = {'id': profile_id, 'name': request.name.strip(), 'vehicle': request.vehicle.model_dump(mode='json')}
    with _lock:
        engine = _engine()
        if engine is None:
            if not create and profile_id not in _profile_cache:
                raise HTTPException(404, 'Vehicle profile not found')
            _profile_cache[profile_id] = payload
        else:
            with Session(engine) as db:
                row = db.get(VehicleProfileRow, profile_id)
                if row is None:
                    if not create:
                        raise HTTPException(404, 'Vehicle profile not found')
                    row = VehicleProfileRow(id=profile_id, payload=payload)
                    db.add(row)
                else:
                    row.payload = payload
                db.commit()
    return payload


@router.post('/vehicle-profiles', status_code=201)
def create_profile(request: ProfileRequest):
    return _save_profile(str(uuid4()), request, True)


@router.put('/vehicle-profiles/{profile_id}')
def update_profile(profile_id: str, request: ProfileRequest):
    return _save_profile(profile_id, request, False)


@router.delete('/vehicle-profiles/{profile_id}')
def delete_profile(profile_id: str):
    with _lock:
        engine = _engine()
        if engine is None:
            if _profile_cache.pop(profile_id, None) is None:
                raise HTTPException(404, 'Vehicle profile not found')
        else:
            with Session(engine) as db:
                row = db.get(VehicleProfileRow, profile_id)
                if row is None:
                    raise HTTPException(404, 'Vehicle profile not found')
                db.delete(row)
                db.commit()
    return {'deleted': True}


def private_report(value):
    if isinstance(value, dict):
        return {key: private_report(item) for key, item in value.items() if key not in {'session_id', 'connected_device_id'}}
    if isinstance(value, list):
        return [private_report(item) for item in value]
    return value


@router.get('/sessions/{session_id}/report')
def report(session_id: str, format: str = Query('json', pattern='^(json|pdf)$'), language: str = 'en'):
    if session_id not in sessions:
        raise HTTPException(404, 'Session not found')
    from diagnostic.localization import localize_session_analysis
    session = localize_session_analysis(sessions[session_id], language=language)
    if hasattr(session, 'model_dump'):
        session = session.model_dump(mode='json')
    # Strip internal identifier values too, including user-independent audit text.
    data = private_report(session)
    def redact(value):
        if isinstance(value, str): return value.replace(session_id, '[internal]')
        if isinstance(value, list): return [redact(v) for v in value]
        if isinstance(value, dict): return {k: redact(v) for k, v in value.items()}
        return value
    data = redact(data)
    if format == 'json':
        return data
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    with _lock:
        if 'ScannerUnicode' not in pdfmetrics.getRegisteredFontNames():
            font = Path(__file__).resolve().parents[1] / 'resources/fonts/DejaVuSans.ttf'
            if not font.is_file():
                import sys
                font = Path(getattr(sys, '_MEIPASS', '.')) / 'backend/resources/fonts/DejaVuSans.ttf'
            pdfmetrics.registerFont(TTFont('ScannerUnicode', str(font)))
    style = ParagraphStyle('body', fontName='ScannerUnicode', fontSize=10, leading=15, wordWrap='CJK')
    labels = {
        'hy': ['Ախտորոշման հաշվետվություն', 'Մեքենա', 'Ախտանիշներ', 'Վարկածներ', 'Առաջարկվող թեստեր', 'Թեստերի արդյունքներ'],
        'ru': ['Диагностический отчёт', 'Автомобиль', 'Симптомы', 'Гипотезы', 'Рекомендуемые тесты', 'Результаты тестов'],
    }.get(language, ['Diagnostic report', 'Vehicle', 'Symptoms', 'Hypotheses', 'Recommended tests', 'Test results'])
    title_style = ParagraphStyle('title', parent=style, fontSize=19, leading=25, textColor=HexColor('#0B3458'))
    heading_style = ParagraphStyle('heading', parent=style, fontSize=12, leading=18, textColor=HexColor('#0B567F'), spaceBefore=10, spaceAfter=7)
    field_labels = {
        'hy': {'raw_text':'Նկարագրություն', 'symptom':'Ախտանիշ', 'fact':'Դիտարկում', 'source':'Աղբյուր', 'confidence':'Վստահություն', 'make':'Արտադրող', 'model':'Մոդել', 'chassis':'Թափք', 'year':'Տարի', 'engine':'Շարժիչ', 'fuel':'Վառելիք', 'ecu':'ECU', 'name':'Անվանում', 'purpose':'Նպատակ', 'category':'Կատեգորիա', 'statement':'Վարկած', 'confidence_score':'Գնահատական', 'status':'Կարգավիճակ', 'result':'Արդյունք', 'result_label':'Արդյունքի անվանում', 'test_name':'Թեստ', 'measurements':'Չափումներ', 'notes':'Նշումներ'},
        'ru': {'raw_text':'Описание', 'symptom':'Симптом', 'fact':'Наблюдение', 'source':'Источник', 'confidence':'Уверенность', 'make':'Марка', 'model':'Модель', 'chassis':'Кузов', 'year':'Год', 'engine':'Двигатель', 'fuel':'Топливо', 'ecu':'ЭБУ', 'name':'Название', 'purpose':'Цель', 'category':'Категория', 'statement':'Гипотеза', 'confidence_score':'Оценка', 'status':'Состояние', 'result':'Результат', 'result_label':'Название результата', 'test_name':'Тест', 'measurements':'Измерения', 'notes':'Примечания'},
    }.get(language, {})
    story = [Paragraph('AI CAR SCANNER', heading_style), Paragraph(escape(labels[0]), title_style), Spacer(1, 16)]
    import json
    for title, key in zip(labels[1:], ['vehicle', 'symptoms', 'hypotheses', 'recommendations', 'test_results']):
        story.append(Paragraph(escape(title), heading_style))
        values = data.get(key) or []
        if not isinstance(values, list): values = [values]
        for value in values:
            # Render each field separately so large reports paginate cleanly.
            fields = value.items() if isinstance(value, dict) else [('value', value)]
            for field, content in fields:
                if field in {'id', 'metadata', 'normalized', 'source_ref', 'supporting_evidence_ids', 'contradicting_evidence_ids', 'target_hypotheses'} or (field == 'test_id' and isinstance(value, dict) and value.get('test_name')):
                    continue
                if content is None:
                    text = '—'
                elif isinstance(content, list) and all(isinstance(item, str) for item in content):
                    text = ', '.join(content) or '—'
                else:
                    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
                label = field_labels.get(field, field.replace('_', ' ').capitalize())
                story.append(Paragraph(escape(f'{label}: {text}'), style))
            story.append(Spacer(1, 7))
        story.append(Spacer(1, 12))
    extra_titles = {'hy': ('Ապացույցներ', 'Գործողությունների պատմություն'), 'ru': ('Доказательства', 'История действий')}.get(language, ('Evidence', 'Activity'))
    for title, key in zip(extra_titles, ('evidence', 'audit_log')):
        story.append(Paragraph(escape(title), heading_style))
        for item in data.get(key, []):
            if key == 'evidence':
                text = str(item.get('fact') or '—')
                details = ' • '.join(str(item[k]) for k in ('status', 'source') if item.get(k))
                if details: text += ' — ' + details
            else:
                text = str(item.get('event') or '—')
                details = ', '.join(f'{k.replace("_", " ")}: {v}' for k, v in item.items() if k != 'event' and isinstance(v, (int, float)))
                if details: text += ' • ' + details
            story.append(Paragraph(escape(text), style))
        story.append(Spacer(1, 12))
    story.append(Paragraph('DTC', heading_style))
    for dtc in data.get('dtcs', []):
        story.append(Paragraph(escape(str(dtc.get('code', '')) + ' ' + str(dtc.get('description') or '')), style))
    output = BytesIO()
    SimpleDocTemplate(output, title=labels[0], author='AI CAR SCANNER').build(story)
    return Response(output.getvalue(), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="diagnostic-report.pdf"'})
