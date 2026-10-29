"""Object-scoped business services. No transport, payment or provider side effects."""
from datetime import timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from professional_platform.models import Role
from diagnostic.models import DiagnosticSession, Vehicle, Symptom, DTC
from ai.reasoning.engine import DiagnosticIntelligenceEngine
from .errors import DomainError
from .models import Account, Consent, Ownership, profiles, utcnow
from .business_models import DiagnosticRecord, Merchant, Product, Offer, Settings, Notification, MonitoringSchedule, MonitoringRun
from .service import as_utc, current_roles, record, staff_access


def require_role(db, actor, role):
    if role not in current_roles(db,actor):raise DomainError('forbidden')


def owner(db, actor, profile_id):
    row=db.get(Ownership,profile_id)
    if row is None or row.account_id!=actor.id:raise DomainError('not_found',404)
    return row


def vehicle_access(db,actor,profile_id,scope,center_id=None,write=False):
    row=db.get(Ownership,profile_id)
    if row is None:raise DomainError('not_found',404)
    if center_id is None:
        owner(db,actor,profile_id)
    else:
        staff_access(db,actor,center_id,Role.TECHNICIAN if write else Role.VIEWER)
        grant=db.scalar(select(Consent).where(Consent.center_id==center_id,Consent.profile_id==profile_id))
        account=db.get(Account,row.account_id)
        if (grant is None or grant.owner_id!=row.account_id or grant.revoked or
            as_utc(grant.expires_at)<=utcnow() or scope not in grant.scopes or account is None or not account.active):
            raise DomainError('not_found',404)
    payload=db.scalar(select(profiles.c.payload).where(profiles.c.id==profile_id))
    if payload is None:raise DomainError('not_found',404)
    return payload


def new_diagnostic(db,actor,data):
    payload=vehicle_access(db,actor,str(data.profile_id),'diagnostic:write',str(data.center_id) if data.center_id else None,True)
    # The canonical model/engine is reused, not forked by role or organization.
    session=DiagnosticSession(vehicle=Vehicle.model_validate({k:v for k,v in payload['vehicle'].items() if k!='metadata'}))
    row=DiagnosticRecord(id=str(session.session_id),profile_id=str(data.profile_id),actor_id=actor.id,
        center_id=str(data.center_id) if data.center_id else None,payload=session.model_dump(mode='json'))
    db.add(row);record(db,actor,'DIAGNOSTIC_CREATED',row.id);db.commit()
    return row


def diagnostic(db,actor,session_id,write=False,scope='report:read'):
    row=db.get(DiagnosticRecord,session_id)
    if row is None:raise DomainError('not_found',404)
    ownership=db.get(Ownership,row.profile_id)
    center=None if ownership and ownership.account_id==actor.id else row.center_id
    # A personal session has no workshop capability. Admin has no implicit bypass.
    vehicle_access(db,actor,row.profile_id,'diagnostic:write' if write else scope,center,write)
    return row


def analyze(db,actor,row,evidence=None,test=None):
    session=DiagnosticSession.model_validate(row.payload);engine=DiagnosticIntelligenceEngine()
    if evidence is not None:
        if evidence.symptom:session.symptoms.append(Symptom(raw_text=evidence.symptom))
        existing={d.code for d in session.dtcs}
        session.dtcs.extend(DTC(code=code) for code in evidence.dtcs if code not in existing)
    if test is not None:
        test_id,data=test
        if not any(str(t.id)==test_id for t in session.recommendations):raise DomainError('not_found',404)
        # UNKNOWN has the existing incomplete/no-conclusion semantics, never FAIL.
        engine.record_test_result(session,test_id,'INCOMPLETE' if data.result=='UNKNOWN' else data.result,data.measurements,data.notes)
    else:engine.analyze(session)
    row.payload=session.model_dump(mode='json');record(db,actor,'DIAGNOSTIC_ANALYZED',row.id);db.commit()
    return row


def merchant_access(db,actor,merchant_id):
    require_role(db,actor,'MARKET');row=db.get(Merchant,merchant_id)
    if row is None or row.owner_id!=actor.id or not row.active:raise DomainError('not_found',404)
    return row


def product_access(db,actor,product_id):
    row=db.get(Product,product_id)
    if row is None:raise DomainError('not_found',404)
    merchant_access(db,actor,row.merchant_id)
    return row


def product_view(row):
    return dict(id=row.id,merchant_id=row.merchant_id,**row.payload,price_minor=row.price_minor,currency=row.currency,
                stock=row.stock,listed=row.listed,moderation=row.moderation,compatibility_status='SELLER_CLAIM_UNVERIFIED')


def public_product(db,product_id):
    row=db.get(Product,product_id);merchant=db.get(Merchant,row.merchant_id) if row else None
    seller=db.get(Account,merchant.owner_id) if merchant else None
    if row is None or merchant is None or seller is None or not seller.active or not merchant.active or not merchant.verified or not row.listed or row.moderation!='APPROVED':
        raise DomainError('not_found',404)
    return row


def save_product(db,actor,merchant_id,data,row=None):
    merchant_access(db,actor,merchant_id)
    values=data.model_dump(mode='json');fields={k:values.pop(k) for k in ('price_minor','currency','stock','listed')}
    if row is None:row=Product(merchant_id=merchant_id);db.add(row)
    row.payload=values
    for key,value in fields.items():setattr(row,key,value)
    # Every update needs moderation again; no approved content substitution.
    row.moderation='PENDING';db.flush();record(db,actor,'PRODUCT_UPDATED',row.id);db.commit()
    return product_view(row)


def matches(fitment,vehicle):
    return (all(str(fitment[k]).casefold()==str(vehicle.get(k,'')).casefold() for k in ('make','model','engine'))
            and fitment['year_from']<=vehicle.get('year',0)<=fitment['year_to'])


def quote(db,actor,product_id,data):
    row=public_product(db,product_id)
    if data.quantity>row.stock:raise DomainError('conflict',409)
    center=None
    if data.center_id:
        center=staff_access(db,actor,str(data.center_id))
        if not center.verified:raise DomainError('forbidden')
    now=utcnow();best=0;offer_id=None
    for offer in db.scalars(select(Offer).where(Offer.product_id==row.id)):
        if not as_utc(offer.starts_at)<=now<as_utc(offer.ends_at) or data.quantity<offer.minimum_quantity:continue
        if offer.coupon and offer.coupon!=data.coupon:continue
        if offer.audience!='PUBLIC' and center is None:continue
        if offer.audience=='CENTER' and offer.center_id!=center.id:continue
        if offer.basis_points>best:best=offer.basis_points;offer_id=offer.id
    subtotal=row.price_minor*data.quantity
    # Single best eligible discount; round discount DOWN to a minor unit.
    discount=subtotal*best//10000
    compatibility='UNKNOWN'
    if data.profile_id:
        ownership=db.get(Ownership,str(data.profile_id))
        shared_center=center.id if center and ownership and ownership.account_id!=actor.id else None
        payload=vehicle_access(db,actor,str(data.profile_id),'vehicle:read',shared_center)
        compatibility='SELLER_CLAIM_UNVERIFIED' if any(matches(f,payload['vehicle']) for f in row.payload['compatibility']) else 'NO_MATCHING_CLAIM'
    record(db,actor,'MARKET_QUOTED',row.id);db.commit()
    return dict(product_id=row.id,quantity=data.quantity,currency=row.currency,subtotal_minor=subtotal,
                discount_minor=discount,total_minor=subtotal-discount,offer_id=offer_id,compatibility=compatibility,
                checkout_available=False,stock_reserved=False)


def settings(db,actor):
    from .business_schemas import SettingsInput
    row=db.get(Settings,actor.id)
    return SettingsInput.model_validate(row.payload if row else dict(language=actor.language,timezone=actor.timezone)).model_dump()


def save_settings(db,actor,data):
    row=db.get(Settings,actor.id)
    if row is None:row=Settings(account_id=actor.id);db.add(row)
    row.payload=data.model_dump()
    # Legacy Account language constraint is preserved; full preference lives here.
    actor.language=data.language if data.language!='fr' else 'en';actor.timezone=data.timezone
    record(db,actor,'SETTINGS_UPDATED',actor.id);db.commit();return settings(db,actor)


def next_due(data,now):
    if data.cadence=='CUSTOM':return now+timedelta(minutes=data.custom_interval_minutes)
    local=now.astimezone(ZoneInfo(data.timezone));target=local.replace(hour=data.hour,minute=0,second=0,microsecond=0)
    if target<=local:target+=timedelta(days=7 if data.cadence=='WEEKLY' else 1)
    return target.astimezone(ZoneInfo('UTC'))


def schedule(db,actor,data):
    owner(db,actor,str(data.profile_id))
    row=db.scalar(select(MonitoringSchedule).where(MonitoringSchedule.owner_id==actor.id,MonitoringSchedule.profile_id==str(data.profile_id)))
    if row is None:row=MonitoringSchedule(owner_id=actor.id,profile_id=str(data.profile_id));db.add(row)
    row.enabled=data.enabled;row.payload=data.model_dump(mode='json');row.next_due=next_due(data,utcnow())
    db.flush();record(db,actor,'MONITORING_SCHEDULE_UPDATED',row.id);db.commit();return row


def dispatch(db,actor,schedule_id):
    row=db.get(MonitoringSchedule,schedule_id)
    if row is None or row.owner_id!=actor.id:raise DomainError('not_found',404)
    owner(db,actor,row.profile_id)
    if not row.enabled or not row.payload.get('consent'):raise DomainError('forbidden')
    if as_utc(row.next_due)>utcnow():raise DomainError('conflict',409)
    run=db.scalar(select(MonitoringRun).where(MonitoringRun.schedule_id==row.id,MonitoringRun.due_at==row.next_due))
    if run:return run
    # No gateway is configured: NEVER synthesize measurements or execute ECU writes.
    run=MonitoringRun(schedule_id=row.id,due_at=row.next_due,status='MISSED' if utcnow()-as_utc(row.next_due)>timedelta(days=1) else 'DEFERRED',reason='NO_CONNECTED_AUTHORIZED_GATEWAY')
    db.add(run);db.flush();record(db,actor,'MONITORING_DEFERRED',run.id)
    db.add(Notification(account_id=actor.id,kind='MONITORING_DEFERRED',payload={'run_id':run.id,'external_delivery':'UNAVAILABLE'}))
    db.commit();return run


def localized_session(db,actor,row,response=None):
    """Translate a detached response copy; never translate persisted domain keys."""
    from diagnostic.localization import localize_session_analysis
    requested=settings(db,actor)['language']
    effective=requested if requested in {'en','hy','ru'} else 'en'
    if response is not None:
        response.headers['Content-Language']=effective
        response.headers['X-Language-Fallback']='true' if requested!=effective else 'false'
    return localize_session_analysis(DiagnosticSession.model_validate(row.payload),effective)
