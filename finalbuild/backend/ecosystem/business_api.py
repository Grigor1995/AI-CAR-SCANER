"""Authenticated business workflows; installed beneath the existing v2 boundary."""
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select, func, update, delete
from professional_platform.models import Role
from .api import PREFIX, current, get_db, require_enabled
from . import business_schemas as S, business_service as B
from .business_models import (DiagnosticRecord, StaffInvitation, WorkOrder, Merchant, Product,
                             Offer, MonitoringSchedule, MonitoringRun, Notification, DirectoryDetails, TechnicalReference)
from .models import Account, AccountRole, AuthSession, ServiceCenter, Staff, Ownership, Consent, AuditEvent, utcnow
from .service import record, current_roles, staff_access, as_utc
from .errors import DomainError
from .schemas import ErrorOutput

router=APIRouter(prefix=PREFIX,tags=['business-ecosystem'],dependencies=[Depends(require_enabled)],responses={status:{'model':ErrorOutput} for status in (401,403,404,409,422,503)})


def fields(row,*names):return {key:getattr(row,key) for key in names}


@router.get('/settings',response_model=S.SettingsInput)
def get_settings(auth=Depends(current),db=Depends(get_db)):
    return B.settings(db,auth.account)


@router.put('/settings',response_model=S.SettingsInput)
def put_settings(data:S.SettingsInput,auth=Depends(current),db=Depends(get_db)):
    return B.save_settings(db,auth.account,data)


@router.post('/diagnostics',status_code=201,response_model=S.DiagnosticOutput)
def create_diagnostic(data:S.NewDiagnostic,auth=Depends(current),db=Depends(get_db)):
    row=B.new_diagnostic(db,auth.account,data);return {'id':row.id,'session':row.payload}


@router.get('/vehicles/{profile_id}/diagnostics')
def history(profile_id:UUID,center_id:UUID|None=None,auth=Depends(current),db=Depends(get_db)):
    center=str(center_id) if center_id else None
    B.vehicle_access(db,auth.account,str(profile_id),'history:read',center)
    rows=db.scalars(select(DiagnosticRecord).where(DiagnosticRecord.profile_id==str(profile_id)).order_by(DiagnosticRecord.created_at.desc()).limit(100))
    # Workshops only see sessions explicitly associated with that workshop.
    result=[fields(row,'id','created_at','version') for row in rows if center is None or row.center_id==center]
    record(db,auth.account,'DIAGNOSTIC_HISTORY_READ',profile_id);db.commit();return result


@router.get('/diagnostics/{session_id}',response_model=S.DiagnosticOutput)
def get_diagnostic(session_id:UUID,response:Response,auth=Depends(current),db=Depends(get_db)):
    row=B.diagnostic(db,auth.account,str(session_id));record(db,auth.account,'DIAGNOSTIC_READ',row.id);db.commit()
    return {'id':row.id,'session':B.localized_session(db,auth.account,row,response),'version':row.version}


@router.post('/diagnostics/{session_id}/analyze',response_model=S.DiagnosticSession)
def analyze(session_id:UUID,data:S.EvidenceInput,response:Response,auth=Depends(current),db=Depends(get_db)):
    row=B.diagnostic(db,auth.account,str(session_id),True)
    B.analyze(db,auth.account,row,data)
    return B.localized_session(db,auth.account,row,response)


@router.post('/diagnostics/{session_id}/tests/{test_id}',response_model=S.DiagnosticSession)
def test_result(session_id:UUID,test_id:UUID,data:S.TestInput,response:Response,auth=Depends(current),db=Depends(get_db)):
    row=B.diagnostic(db,auth.account,str(session_id),True)
    B.analyze(db,auth.account,row,test=(str(test_id),data))
    return B.localized_session(db,auth.account,row,response)


@router.get('/diagnostics/{session_id}/obd-plan')
def obd_plan(session_id:UUID,auth=Depends(current),db=Depends(get_db)):
    B.diagnostic(db,auth.account,str(session_id),True)
    from obd.decoding import polling_plan
    return polling_plan()


@router.post('/diagnostics/{session_id}/live')
def bridge(session_id:UUID,data:S.BridgeInput,auth=Depends(current),db=Depends(get_db)):
    row=B.diagnostic(db,auth.account,str(session_id),True)
    from obd.decoding import decode_snapshot
    decoded=decode_snapshot(data.responses)
    # Only successful observed channels; missing measurements remain null, not zero.
    payload=dict(row.payload);samples=list(payload.get('live_data',[]))
    latest={'timestamp_ms':data.timestamp_ms,**decoded}
    samples.append(latest);payload['live_data']=samples[-1000:]
    row.payload=payload;record(db,auth.account,'NATIVE_BRIDGE_OBSERVED',row.id);db.commit()
    return latest


@router.get('/diagnostics/{session_id}/live')
def live(session_id:UUID,auth=Depends(current),db=Depends(get_db)):
    row=B.diagnostic(db,auth.account,str(session_id),scope='live:read')
    record(db,auth.account,'LIVE_DATA_READ',row.id);db.commit()
    samples=row.payload.get('live_data',[])
    return samples[-1] if samples else {'available':False}


@router.post('/service-centers/{center_id}/staff-invitations',status_code=201)
def invite_staff(center_id:UUID,data:S.StaffInviteInput,auth=Depends(current),db=Depends(get_db)):
    staff_access(db,auth.account,str(center_id),Role.OWNER)
    target=db.get(Account,str(data.account_id))
    if target is None or not target.active:raise DomainError('not_found',404)
    if db.get(Staff,(str(center_id),str(data.account_id))):raise DomainError('conflict',409)
    row=StaffInvitation(center_id=str(center_id),account_id=str(data.account_id),role=data.role,expires_at=utcnow()+timedelta(days=7))
    db.add(row);db.flush();record(db,auth.account,'STAFF_INVITED',row.id);db.commit()
    return fields(row,'id','expires_at','role')


@router.get('/staff-invitations')
def staff_inbox(auth=Depends(current),db=Depends(get_db)):
    return [fields(row,'id','center_id','role','expires_at','accepted') for row in db.scalars(select(StaffInvitation).where(StaffInvitation.account_id==auth.account.id))]


@router.post('/staff-invitations/{invitation_id}/accept')
def accept_staff(invitation_id:UUID,auth=Depends(current),db=Depends(get_db)):
    row=db.get(StaffInvitation,str(invitation_id));center=db.get(ServiceCenter,row.center_id) if row else None
    if row is None or row.account_id!=auth.account.id or center is None or not center.active:raise DomainError('not_found',404)
    if as_utc(row.expires_at)<=utcnow() or row.accepted:raise DomainError('conflict',409)
    result=db.execute(update(StaffInvitation).where(StaffInvitation.id==row.id,StaffInvitation.accepted.is_(False),StaffInvitation.expires_at>utcnow()).values(accepted=True).execution_options(synchronize_session=False))
    if result.rowcount!=1:raise DomainError('conflict',409)
    db.add(Staff(center_id=row.center_id,account_id=auth.account.id,role=row.role))
    if 'CUSTOMER' not in current_roles(db,auth.account):db.add(AccountRole(account_id=auth.account.id,role='CUSTOMER'))
    record(db,auth.account,'STAFF_ACCEPTED',row.id);db.commit();return {'accepted':True}


@router.delete('/service-centers/{center_id}/staff/{account_id}',status_code=204)
def remove_staff(center_id:UUID,account_id:UUID,auth=Depends(current),db=Depends(get_db)):
    staff_access(db,auth.account,str(center_id),Role.OWNER);row=db.get(Staff,(str(center_id),str(account_id)))
    if row is None:raise DomainError('not_found',404)
    if row.role=='owner':raise DomainError('forbidden')
    row.active=False;record(db,auth.account,'STAFF_DISABLED',account_id);db.commit();return Response(status_code=204)


@router.post('/service-centers/{center_id}/work-orders',status_code=201,response_model=S.WorkOrderOutput)
def new_order(center_id:UUID,data:S.OrderInput,auth=Depends(current),db=Depends(get_db)):
    B.vehicle_access(db,auth.account,str(data.profile_id),'maintenance:write',str(center_id),True)
    row=WorkOrder(center_id=str(center_id),profile_id=str(data.profile_id),title=data.title)
    db.add(row);db.flush();record(db,auth.account,'WORK_ORDER_CREATED',row.id);db.commit()
    return fields(row,'id','title','status','notes')


@router.patch('/work-orders/{order_id}',response_model=S.WorkOrderOutput)
def update_order(order_id:UUID,data:S.OrderPatch,auth=Depends(current),db=Depends(get_db)):
    row=db.get(WorkOrder,str(order_id))
    if row is None:raise DomainError('not_found',404)
    B.vehicle_access(db,auth.account,row.profile_id,'maintenance:write',row.center_id,True)
    if row.status=='COMPLETED' and data.status!='COMPLETED':raise DomainError('conflict',409)
    row.status=data.status;row.notes=data.notes;record(db,auth.account,'WORK_ORDER_UPDATED',row.id);db.commit()
    return fields(row,'id','title','status','notes')


@router.get('/vehicles/{profile_id}/work-orders',response_model=list[S.WorkOrderOutput])
def orders(profile_id:UUID,center_id:UUID|None=None,auth=Depends(current),db=Depends(get_db)):
    center=str(center_id) if center_id else None
    B.vehicle_access(db,auth.account,str(profile_id),'maintenance:read',center)
    rows=db.scalars(select(WorkOrder).where(WorkOrder.profile_id==str(profile_id)).limit(100))
    result=[fields(row,'id','center_id','title','status','notes') for row in rows if center is None or row.center_id==center]
    record(db,auth.account,'WORK_ORDERS_READ',profile_id);db.commit();return result


@router.put('/service-centers/{center_id}/directory')
def directory_update(center_id:UUID,data:S.DirectoryInput,auth=Depends(current),db=Depends(get_db)):
    center=staff_access(db,auth.account,str(center_id),Role.ADMIN)
    row=db.get(DirectoryDetails,str(center_id))
    if row is None:row=DirectoryDetails(center_id=str(center_id));db.add(row)
    row.payload=data.model_dump();center.verified=False
    record(db,auth.account,'DIRECTORY_UPDATED',center_id);db.commit();return {'requires_verification':True}


@router.get('/directory')
def directory(city:str=Query(default='',max_length=100),make:str=Query(default='',max_length=100),engine:str=Query(default='',max_length=100),auth=Depends(current),db=Depends(get_db)):
    result=[]
    for center,details in db.execute(select(ServiceCenter,DirectoryDetails).join(DirectoryDetails).where(ServiceCenter.active.is_(True),ServiceCenter.verified.is_(True)).limit(500)):
        d=details.payload
        if city and city.casefold()!=d['city'].casefold():continue
        if make and make.casefold() not in [m.casefold() for m in d['makes']]:continue
        if engine and engine.casefold() not in [v.casefold() for v in d['engines']]:continue
        result.append({**fields(center,'id','name','address','phone','verified'),**d})
    return result


@router.post('/merchants',status_code=201)
def register_merchant(data:S.MerchantInput,auth=Depends(current),db=Depends(get_db)):
    row=Merchant(owner_id=auth.account.id,**data.model_dump());db.add(row);db.flush()
    if 'MARKET' not in current_roles(db,auth.account):db.add(AccountRole(account_id=auth.account.id,role='MARKET'))
    record(db,auth.account,'MERCHANT_REGISTERED',row.id);db.commit();return fields(row,'id','name','verified')


@router.get('/merchants')
def merchants(auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'MARKET')
    return [fields(r,'id','name','address','verified','active') for r in db.scalars(select(Merchant).where(Merchant.owner_id==auth.account.id))]


@router.get('/merchants/{merchant_id}/products',response_model=list[S.ProductOutput])
def inventory(merchant_id:UUID,auth=Depends(current),db=Depends(get_db)):
    B.merchant_access(db,auth.account,str(merchant_id))
    return [B.product_view(row) for row in db.scalars(select(Product).where(Product.merchant_id==str(merchant_id)).limit(500))]


@router.post('/merchants/{merchant_id}/products',status_code=201,response_model=S.ProductOutput)
def create_product(merchant_id:UUID,data:S.ProductInput,auth=Depends(current),db=Depends(get_db)):
    return B.save_product(db,auth.account,str(merchant_id),data)


@router.put('/products/{product_id}',response_model=S.ProductOutput)
def update_product(product_id:UUID,data:S.ProductInput,auth=Depends(current),db=Depends(get_db)):
    row=B.product_access(db,auth.account,str(product_id));return B.save_product(db,auth.account,row.merchant_id,data,row)


@router.get('/marketplace/products',response_model=list[S.ProductOutput])
def market(auth=Depends(current),db=Depends(get_db)):
    rows=db.scalars(select(Product).join(Merchant).join(Account,Account.id==Merchant.owner_id).where(Account.active.is_(True),Merchant.active.is_(True),Merchant.verified.is_(True),Product.listed.is_(True),Product.moderation=='APPROVED').limit(100))
    return [B.product_view(r) for r in rows]


@router.post('/products/{product_id}/offers',status_code=201)
def offer(product_id:UUID,data:S.OfferInput,auth=Depends(current),db=Depends(get_db)):
    row=B.product_access(db,auth.account,str(product_id));values=data.model_dump()
    if data.center_id:
        center=db.get(ServiceCenter,str(data.center_id))
        if center is None or not center.active or not center.verified:raise DomainError('not_found',404)
        values['center_id']=str(data.center_id)
    deal=Offer(product_id=row.id,**values);db.add(deal);db.flush();record(db,auth.account,'OFFER_CREATED',deal.id);db.commit()
    return {'id':deal.id}


@router.post('/products/{product_id}/quote',response_model=S.QuoteOutput)
def price(product_id:UUID,data:S.QuoteInput,auth=Depends(current),db=Depends(get_db)):
    return B.quote(db,auth.account,str(product_id),data)


@router.put('/monitoring',response_model=S.ScheduleOutput)
def monitoring(data:S.ScheduleInput,auth=Depends(current),db=Depends(get_db)):
    row=B.schedule(db,auth.account,data);return fields(row,'id','next_due','enabled','payload')


@router.get('/monitoring',response_model=list[S.ScheduleOutput])
def schedules(auth=Depends(current),db=Depends(get_db)):
    return [fields(r,'id','profile_id','next_due','enabled','payload') for r in db.scalars(select(MonitoringSchedule).where(MonitoringSchedule.owner_id==auth.account.id))]


@router.post('/monitoring/{schedule_id}/dispatch',response_model=S.RunOutput)
def dispatch(schedule_id:UUID,auth=Depends(current),db=Depends(get_db)):
    return fields(B.dispatch(db,auth.account,str(schedule_id)),'id','status','reason','due_at')


@router.get('/monitoring/{schedule_id}/runs',response_model=list[S.RunOutput])
def runs(schedule_id:UUID,auth=Depends(current),db=Depends(get_db)):
    row=db.get(MonitoringSchedule,str(schedule_id))
    if row is None or row.owner_id!=auth.account.id:raise DomainError('not_found',404)
    return [fields(r,'id','due_at','status','reason') for r in db.scalars(select(MonitoringRun).where(MonitoringRun.schedule_id==row.id).limit(100))]


@router.get('/notifications')
def notifications(auth=Depends(current),db=Depends(get_db)):
    return [fields(r,'id','kind','payload','read','created_at') for r in db.scalars(select(Notification).where(Notification.account_id==auth.account.id).order_by(Notification.created_at.desc()).limit(100))]


@router.post('/notifications/{notification_id}/read')
def read_notification(notification_id:UUID,auth=Depends(current),db=Depends(get_db)):
    row=db.get(Notification,str(notification_id))
    if row is None or row.account_id!=auth.account.id:raise DomainError('not_found',404)
    row.read=True;db.commit();return {'read':True}


@router.post('/admin/references',status_code=201)
def reference(data:S.ReferenceInput,auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN');payload=data.model_dump(mode='json');kind=payload.pop('kind')
    row=TechnicalReference(kind=kind,payload=payload);db.add(row);db.flush();record(db,auth.account,'REFERENCE_REGISTERED',row.id);db.commit();return {'id':row.id}


@router.get('/vehicles/{profile_id}/references')
def references(profile_id:UUID,auth=Depends(current),db=Depends(get_db)):
    payload=B.vehicle_access(db,auth.account,str(profile_id),'vehicle:read')
    return [{'id':r.id,'kind':r.kind,**r.payload} for r in db.scalars(select(TechnicalReference).limit(500)) if B.matches(r.payload['fitment'],payload['vehicle'])]


@router.get('/admin/summary')
def admin_summary(auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN');record(db,auth.account,'ADMIN_AGGREGATE_READ','platform');db.commit()
    return {name:db.scalar(select(func.count()).select_from(model)) for name,model in
            [('accounts',Account),('vehicles',Ownership),('service_centers',ServiceCenter),('merchants',Merchant),
             ('products',Product),('diagnostics',DiagnosticRecord),('monitoring_runs',MonitoringRun),('notifications',Notification)]}


@router.get('/admin/accounts')
def admin_accounts(auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN');record(db,auth.account,'ADMIN_ACCOUNTS_READ','accounts');db.commit()
    return [dict(**fields(r,'id','email','full_name','active'),roles=current_roles(db,r)) for r in db.scalars(select(Account).limit(100))]


@router.patch('/admin/accounts/{account_id}')
def admin_account(account_id:UUID,data:S.AdminAccountPatch,auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN')
    if str(account_id)==auth.account.id:raise DomainError('forbidden')
    row=db.get(Account,str(account_id))
    if row is None:raise DomainError('not_found',404)
    row.active=data.active;db.execute(delete(AccountRole).where(AccountRole.account_id==row.id))
    for role in set(data.roles):db.add(AccountRole(account_id=row.id,role=role))
    db.execute(update(AuthSession).where(AuthSession.account_id==row.id).values(revoked=True))
    record(db,auth.account,'ADMIN_ACCOUNT_CHANGED',row.id);db.commit();return {'updated':True,'sessions_revoked':True}


@router.patch('/admin/service-centers/{center_id}')
def approve_center(center_id:UUID,data:S.Approval,auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN');row=db.get(ServiceCenter,str(center_id))
    if row is None:raise DomainError('not_found',404)
    row.active=data.active;row.verified=data.verified;record(db,auth.account,'ADMIN_CENTER_CHANGED',row.id);db.commit();return fields(row,'id','active','verified')


@router.patch('/admin/merchants/{merchant_id}')
def approve_merchant(merchant_id:UUID,data:S.Approval,auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN');row=db.get(Merchant,str(merchant_id))
    if row is None:raise DomainError('not_found',404)
    row.active=data.active;row.verified=data.verified;record(db,auth.account,'ADMIN_MERCHANT_CHANGED',row.id);db.commit();return fields(row,'id','active','verified')


@router.patch('/admin/products/{product_id}')
def moderate(product_id:UUID,data:S.Moderation,auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN');row=db.get(Product,str(product_id))
    if row is None:raise DomainError('not_found',404)
    row.moderation=data.status;record(db,auth.account,'ADMIN_PRODUCT_MODERATED',row.id);db.commit();return fields(row,'id','moderation')


@router.get('/admin/audit')
def audit(auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,'ADMIN')
    record(db,auth.account,'ADMIN_AUDIT_READ','audit');db.commit()
    return [fields(r,'id','actor_id','action','target_id','created_at') for r in db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100))]


@router.get('/service-centers/{center_id}/dashboard')
def workshop_dashboard(center_id:UUID,auth=Depends(current),db=Depends(get_db)):
    staff_access(db,auth.account,str(center_id))
    grants=list(db.scalars(select(Consent).join(Ownership,Ownership.profile_id==Consent.profile_id)
        .join(Account,Account.id==Consent.owner_id).where(Consent.center_id==str(center_id),Consent.revoked.is_(False),
        Consent.expires_at>utcnow(),Ownership.account_id==Consent.owner_id,Account.active.is_(True))))
    report_profiles={g.profile_id for g in grants if 'report:read' in g.scopes or 'history:read' in g.scopes}
    maintenance_profiles={g.profile_id for g in grants if 'maintenance:read' in g.scopes}
    profiles={g.profile_id for g in grants}
    records=list(db.scalars(select(DiagnosticRecord).where(DiagnosticRecord.center_id==str(center_id),DiagnosticRecord.profile_id.in_(report_profiles)))) if profiles else []
    work=list(db.scalars(select(WorkOrder).where(WorkOrder.center_id==str(center_id),WorkOrder.profile_id.in_(maintenance_profiles)))) if profiles else []
    record(db,auth.account,'WORKSHOP_DASHBOARD_READ',center_id);db.commit()
    return {'connected_users':len({g.owner_id for g in grants}),'connected_vehicles':len(profiles),
        'diagnostic_sessions':len(records),'work_orders':len(work),'completed_repairs':sum(r.status=='COMPLETED' for r in work)}


@router.get('/navigation',response_model=S.NavigationOutput)
def navigation(workspace:str=Query(default='USER',pattern='^(USER|CUSTOMER|ADMIN|MARKET)$'),language:str=Query(default='en',pattern='^(en|hy|ru|fr)$'),auth=Depends(current),db=Depends(get_db)):
    B.require_role(db,auth.account,workspace)
    # MARKET remains a portal. /workspace only accepts the three primary modes.
    pages={
        'USER':[('vehicles','/vehicles'),('monitoring','/monitoring'),('notifications','/notifications'),('directory','/directory'),('products','/marketplace/products'),('settings','/settings')],
        'CUSTOMER':[('centers','/service-centers'),('invitations','/staff-invitations'),('products','/marketplace/products'),('settings','/settings')],
        'ADMIN':[('dashboard','/admin/summary'),('accounts','/admin/accounts'),('audit','/admin/audit'),('settings','/settings')],
        'MARKET':[('merchants','/merchants'),('settings','/settings')]}
    labels={
        'vehicles':('My vehicles','Իմ մեքենաները','Мои автомобили','Mes véhicules'),
        'monitoring':('Monitoring','Մոնիտորինգ','Мониторинг','Surveillance'),
        'notifications':('Notifications','Ծանուցումներ','Уведомления','Notifications'),
        'directory':('Verified services','Ստուգված ծառայություններ','Проверенные сервисы','Services vérifiés'),
        'products':('Marketplace','Ապրանքներ','Маркетплейс','Catalogue'),
        'settings':('Account settings','Հաշվի կարգավորումներ','Настройки аккаунта','Paramètres du compte'),
        'centers':('My workshops','Իմ արհեստանոցները','Мои мастерские','Mes ateliers'),
        'invitations':('Staff invitations','Աշխատակցի հրավերներ','Приглашения сотрудников','Invitations du personnel'),
        'dashboard':('Dashboard','Ամփոփում','Обзор','Tableau de bord'),
        'accounts':('Accounts','Հաշիվներ','Аккаунты','Comptes'),
        'audit':('Audit events','Գործողությունների մատյան','Журнал действий','Journal d’audit'),
        'merchants':('My shops','Իմ խանութները','Мои магазины','Mes boutiques')}
    index={'en':0,'hy':1,'ru':2,'fr':3}[language]
    return {'workspace':workspace,'primary':workspace!='MARKET','pages':[{'key':k,'label':labels[k][index],'path':PREFIX+path} for k,path in pages[workspace]]}
