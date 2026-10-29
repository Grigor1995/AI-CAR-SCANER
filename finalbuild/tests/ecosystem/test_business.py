"""Actual SQL + HTTP business workflows; no mocked permission or pricing checks."""
from datetime import timedelta
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session
from test_foundation import register, vehicle, workshop, sharing, P
from ecosystem.models import AccountRole, utcnow
from ecosystem.business_models import MonitoringSchedule
from ecosystem.units import convert


def admin(engine,account_id):
    with Session(engine) as db:db.add(AccountRole(account_id=account_id,role='ADMIN'));db.commit()


def approved(environment):
    client,engine=environment
    aid,ah=register(client,'admin');admin(engine,aid)
    seller,sh=register(client,'seller')
    merchant=client.post(P+'/merchants',headers=sh,json={'name':'Manual shop','address':'Declared address'}).json()['id']
    product={'name':'Test component','category':'PART','part_number':'TEST-42','price_minor':1999,'currency':'USD',
        'stock':20,'listed':True,'compatibility':[{'make':'Mercedes-Benz','model':'E-Class','engine':'M272','year_from':2000,'year_to':2010}]}
    response=client.post(P+f'/merchants/{merchant}/products',headers=sh,json=product);assert response.status_code==201,response.text
    pid=response.json()['id']
    assert client.get(P+'/marketplace/products',headers=ah).json()==[]
    assert client.patch(P+f'/admin/merchants/{merchant}',headers=ah,json={}).status_code==200
    assert client.patch(P+f'/admin/products/{pid}',headers=ah,json={'status':'APPROVED'}).status_code==200
    return client,engine,ah,sh,merchant,pid,product


def test_owned_shared_diagnostic_recalculation_and_revocation(environment):
    c,e,oid,oh,tid,th,vid,center,inv=sharing(environment)
    grant=c.post(P+f'/invitations/{inv}/accept',headers=oh,json={'profile_id':vid,'scopes':['vehicle:read','report:read','history:read','live:read','diagnostic:write','maintenance:read','maintenance:write']})
    assert grant.status_code==200,grant.text
    created=c.post(P+'/diagnostics',headers=th,json={'profile_id':vid,'center_id':center});assert created.status_code==201,created.text
    sid=created.json()['id'];assert 'private' not in created.text
    analyzed=c.post(P+f'/diagnostics/{sid}/analyze',headers=th,json={'symptom':'Engine shakes on LPG below 2000 RPM under load; petrol is normal.','dtcs':['P0302']})
    assert analyzed.status_code==200,analyzed.text
    assert analyzed.json()['recommendations'] and analyzed.json()['hypotheses']
    test=analyzed.json()['recommendations'][0]['id']
    result=c.post(P+f'/diagnostics/{sid}/tests/{test}',headers=th,json={'result':'FAIL','notes':'Observed test failed'})
    assert result.status_code==200,result.text
    assert len(result.json()['test_results'])==1
    assert any(a['event']=='TEST_RESULT_INTERPRETED' for a in result.json()['audit_log'])
    assert c.get(P+f'/diagnostics/{sid}',headers=oh).status_code==200
    assert c.get(P+f'/vehicles/{vid}/diagnostics',headers=th,params={'center_id':center}).json()[0]['id']==sid
    assert c.get(P+f'/diagnostics/{sid}/obd-plan',headers=th).json()['read_only']
    missing=c.get(P+f'/diagnostics/{sid}/live',headers=th).json();assert missing['available'] is False
    live=c.post(P+f'/diagnostics/{sid}/live',headers=th,json={'timestamp_ms':1000,'responses':{'010C':'41 0C 1A F8 >'}})
    assert live.json()['values']['rpm']==1726 and live.json()['values']['coolant_c'] is None
    assert live.json()['hardware_verified'] is False
    c.post(P+f'/diagnostics/{sid}/analyze',headers=th,json={})
    assert c.get(P+f'/diagnostics/{sid}/live',headers=oh).json()['timestamp_ms']==1000
    order=c.post(P+f'/service-centers/{center}/work-orders',headers=th,json={'profile_id':vid,'title':'Inspect measured misfire'})
    assert order.status_code==201,order.text
    orderid=order.json()['id']
    assert c.patch(P+f'/work-orders/{orderid}',headers=th,json={'status':'COMPLETED','notes':'Documented repair'}).status_code==200
    assert c.patch(P+f'/work-orders/{orderid}',headers=th,json={'status':'OPEN'}).status_code==409
    assert c.get(P+f'/vehicles/{vid}/work-orders',headers=oh).json()[0]['status']=='COMPLETED'
    assert c.get(P+f'/service-centers/{center}/dashboard',headers=th).json()['connected_users']==1
    c.delete(P+'/consents/'+grant.json()['id'],headers=oh)
    assert c.get(P+f'/diagnostics/{sid}',headers=th).status_code==404
    assert c.post(P+f'/diagnostics/{sid}/analyze',headers=th,json={}).status_code==404
    assert c.get(P+f'/vehicles/{vid}/work-orders',headers=th,params={'center_id':center}).status_code==404
    assert c.get(P+f'/service-centers/{center}/dashboard',headers=th).json()['connected_users']==0


def test_personal_sessions_no_admin_bypass_and_unknown_test(environment):
    c,e=environment;oid,oh=register(c);aid,ah=register(c,'admin');admin(e,aid);vid=vehicle(c,oh)
    sid=c.post(P+'/diagnostics',headers=oh,json={'profile_id':vid}).json()['id']
    assert c.get(P+f'/diagnostics/{sid}',headers=ah).status_code==404
    assert c.post(P+f'/diagnostics/{sid}/tests/{uuid4()}',headers=oh,json={'result':'UNKNOWN'}).status_code==404
    assert c.post(P+f'/diagnostics/{sid}/analyze',headers=oh,json={'dtcs':['FFFFF']}).status_code==422
    assert c.post(P+f'/diagnostics/{sid}/live',headers=oh,json={'timestamp_ms':1,'responses':{'010C':'x'*32001}}).status_code==422
    assert c.post(P+'/diagnostics',headers=oh,json={'profile_id':str(uuid4())}).status_code==404


def test_read_consent_never_implies_write(environment):
    c,e,oid,oh,tid,th,vid,center,inv=sharing(environment)
    c.post(P+f'/invitations/{inv}/accept',headers=oh,json={'profile_id':vid})
    assert c.post(P+'/diagnostics',headers=th,json={'profile_id':vid,'center_id':center}).status_code==404
    assert c.post(P+f'/service-centers/{center}/work-orders',headers=th,json={'profile_id':vid,'title':'No permission'}).status_code==404


def test_staff_acceptance_and_disabling(environment):
    c,e=environment;oid,oh=register(c);sid,sh=register(c,'staff');center=workshop(c,oh)
    inv=c.post(P+f'/service-centers/{center}/staff-invitations',headers=oh,json={'account_id':sid,'role':'viewer'})
    assert inv.status_code==201,inv.text
    iid=inv.json()['id']
    assert c.get(P+'/staff-invitations',headers=sh).json()[0]['id']==iid
    assert c.post(P+f'/staff-invitations/{iid}/accept',headers=oh).status_code==404
    assert c.post(P+f'/staff-invitations/{iid}/accept',headers=sh).status_code==200
    assert c.post(P+f'/staff-invitations/{iid}/accept',headers=sh).status_code==409
    assert c.get(P+f'/service-centers/{center}/dashboard',headers=sh).status_code==200
    assert c.post(P+f'/service-centers/{center}/staff-invitations',headers=sh,json={'account_id':oid,'role':'admin'}).status_code==403
    assert c.delete(P+f'/service-centers/{center}/staff/{oid}',headers=oh).status_code==403
    assert c.delete(P+f'/service-centers/{center}/staff/{sid}',headers=oh).status_code==204
    assert c.get(P+f'/service-centers/{center}/dashboard',headers=sh).status_code==404


def test_market_moderation_quotes_and_no_checkout(environment):
    c,e,ah,sh,merchant,pid,payload=approved(environment)
    uid,uh=register(c,'buyer');vid=vehicle(c,uh)
    start=utcnow()-timedelta(days=1);end=utcnow()+timedelta(days=1)
    for discount,audience,coupon in [(1000,'PUBLIC',None),(2000,'PUBLIC','SAVE20'),(5000,'CUSTOMER',None)]:
        deal=c.post(P+f'/products/{pid}/offers',headers=sh,json={'basis_points':discount,'audience':audience,'coupon':coupon,'starts_at':start.isoformat(),'ends_at':end.isoformat()})
        assert deal.status_code==201,deal.text
    q=c.post(P+f'/products/{pid}/quote',headers=uh,json={'quantity':2,'profile_id':vid}).json()
    assert q['subtotal_minor']==3998 and q['discount_minor']==399 and q['total_minor']==3599
    assert q['compatibility']=='SELLER_CLAIM_UNVERIFIED' and q['checkout_available'] is False
    assert c.post(P+f'/products/{pid}/quote',headers=uh,json={'coupon':'SAVE20'}).json()['discount_minor']==399
    assert c.post(P+f'/products/{pid}/quote',headers=uh,json={'quantity':100}).status_code==409
    assert c.put(P+f'/products/{pid}',headers=uh,json=payload).status_code==403
    center=workshop(c,uh)
    assert c.post(P+f'/products/{pid}/quote',headers=uh,json={'center_id':center}).status_code==403
    c.patch(P+f'/admin/service-centers/{center}',headers=ah,json={})
    assert c.post(P+f'/products/{pid}/quote',headers=uh,json={'center_id':center}).json()['discount_minor']==999
    assert c.put(P+f'/products/{pid}',headers=sh,json=payload).json()['moderation']=='PENDING'
    assert c.get(P+'/marketplace/products',headers=uh).json()==[]
    assert len(c.get(P+f'/merchants/{merchant}/products',headers=sh).json())==1
    assert c.post(P+'/workspace',headers=sh,json={'mode':'MARKET'}).status_code==422
    assert c.get(P+'/me',headers=sh).json()['portals']==['MARKET']


def test_admin_suspend_revokes_sessions_and_no_self_lockout(environment):
    c,e=environment;aid,ah=register(c,'admin');uid,uh=register(c);admin(e,aid)
    assert c.get(P+'/admin/summary',headers=uh).status_code==403
    assert c.patch(P+f'/admin/accounts/{aid}',headers=ah,json={'active':False,'roles':['USER']}).status_code==403
    result=c.patch(P+f'/admin/accounts/{uid}',headers=ah,json={'active':False,'roles':['USER']})
    assert result.json()['sessions_revoked']
    assert c.get(P+'/me',headers=uh).status_code==401
    assert c.get(P+'/admin/summary',headers=ah).json()['accounts']==2
    assert len(c.get(P+'/admin/accounts',headers=ah).json())==2
    assert any(row['action']=='ADMIN_ACCOUNT_CHANGED' for row in c.get(P+'/admin/audit',headers=ah).json())


def test_settings_monitoring_deferred_idempotent_and_notifications(environment):
    c,e=environment;uid,uh=register(c);vid=vehicle(c,uh)
    settings=c.put(P+'/settings',headers=uh,json={'language':'fr','units':'USA','timezone':'Asia/Yerevan','sms_alerts':True})
    assert settings.status_code==200,settings.text
    assert c.get(P+'/settings',headers=uh).json()['language']=='fr'
    assert c.get(P+'/admin/summary',headers={**uh,'Accept-Language':'fr'}).json()['detail']=='Accès refusé.'
    scheduled=c.put(P+'/monitoring',headers=uh,json={'profile_id':vid,'consent':True,'timezone':'Asia/Yerevan'})
    assert scheduled.status_code==200,scheduled.text
    schedule=scheduled.json()['id'];assert scheduled.json()['payload']['cadence']=='DAILY'
    assert c.post(P+f'/monitoring/{schedule}/dispatch',headers=uh).status_code==409
    with Session(e) as db:
        row=db.get(MonitoringSchedule,schedule);row.next_due=utcnow()-timedelta(minutes=10);db.commit()
    run=c.post(P+f'/monitoring/{schedule}/dispatch',headers=uh).json();assert run['status']=='DEFERRED'
    assert c.post(P+f'/monitoring/{schedule}/dispatch',headers=uh).json()['id']==run['id']
    assert len(c.get(P+f'/monitoring/{schedule}/runs',headers=uh).json())==1
    notification=c.get(P+'/notifications',headers=uh).json()[0]
    assert notification['payload']['external_delivery']=='UNAVAILABLE'
    assert c.post(P+'/notifications/'+notification['id']+'/read',headers=uh).json()['read']
    assert len(c.get(P+'/monitoring',headers=uh).json())==1
    assert c.put(P+'/monitoring',headers=uh,json={'profile_id':vid,'consent':False}).status_code==422
    assert c.put(P+'/settings',headers=uh,json={'timezone':'Invented/Zone'}).status_code==422


def test_verified_directory_and_licensed_references(environment):
    c,e=environment;uid,uh=register(c);aid,ah=register(c,'admin');admin(e,aid);vid=vehicle(c,uh);center=workshop(c,uh)
    assert c.put(P+f'/service-centers/{center}/directory',headers=uh,json={'city':'Yerevan','makes':['Mercedes-Benz'],'engines':['M272']}).status_code==200
    assert c.get(P+'/directory',headers=uh).json()==[]
    c.patch(P+f'/admin/service-centers/{center}',headers=ah,json={})
    assert len(c.get(P+'/directory',headers=uh,params={'city':'Yerevan','make':'Mercedes-Benz','engine':'M272'}).json())==1
    assert c.get(P+'/directory',headers=uh,params={'city':'Paris'}).json()==[]
    assert c.get(P+f'/vehicles/{vid}/references',headers=uh).json()==[]
    reference={'kind':'REPAIR','title':'Authorized fixture reference','fitment':{'make':'Mercedes-Benz','model':'E-Class','engine':'M272','year_from':2000,'year_to':2010},'source_url':'https://example.invalid/authorized-fixture','license':'Test fixture permission, not production repair data','instructions':'Fixture only, not vehicle repair instructions.','safety_warnings':['Seek a qualified professional.']}
    assert c.post(P+'/admin/references',headers=uh,json=reference).status_code==403
    assert c.post(P+'/admin/references',headers=ah,json=reference).status_code==201
    assert len(c.get(P+f'/vehicles/{vid}/references',headers=uh).json())==1


@pytest.mark.parametrize('value,quantity,unit,expected',[(100,'speed','mph',62.137119),(0,'temperature','F',32),(100,'pressure','bar',1),(8,'consumption','mpg_US',29.401823),(100,'distance','miles',62.137119),(1,'power','hp',1.341022),(1,'volume','US_gallons',.264172),(1,'torque','lb-ft',.737562),(8,'consumption','km/L',12.5)])
def test_engineering_conversion(value,quantity,unit,expected):
    assert convert(value,quantity,unit)==pytest.approx(expected,rel=1e-5)


@pytest.mark.parametrize('value,quantity,unit',[(0,'consumption','mpg_US'),(float('nan'),'speed','mph'),(1,'power','invalid'),(1,'consumption','invalid')])
def test_invalid_units(value,quantity,unit):
    with pytest.raises(ValueError):convert(value,quantity,unit)


def test_navigation_enforces_three_modes_and_merchant_portal(environment):
    c,e=environment;uid,uh=register(c)
    for language,label in [('en','My vehicles'),('hy','Իմ մեքենաները'),('ru','Мои автомобили'),('fr','Mes véhicules')]:
        nav=c.get(P+'/navigation',headers=uh,params={'language':language}).json()
        assert nav['primary'] is True and nav['pages'][0]['label']==label
    assert c.get(P+'/navigation?workspace=ADMIN',headers=uh).status_code==403
    assert c.get(P+'/navigation?workspace=OTHER',headers=uh).status_code==422
    c.post(P+'/merchants',headers=uh,json={'name':'Shop','address':'Address'})
    assert c.get(P+'/navigation?workspace=MARKET',headers=uh).json()['primary'] is False
    assert c.get(P+'/merchants',headers=uh).status_code==200
    workshop(c,uh)
    assert c.get(P+'/navigation?workspace=CUSTOMER',headers=uh).status_code==200
    admin(e,uid)
    assert c.get(P+'/navigation?workspace=ADMIN',headers=uh).json()['pages'][0]['path'].endswith('/admin/summary')


def test_mutation_negative_boundaries_and_missing_objects(environment):
    c,e=environment;uid,uh=register(c);aid,ah=register(c,'admin');admin(e,aid);missing=str(uuid4())
    assert c.get(P+'/merchants',headers=uh).status_code==403
    for path in [f'/diagnostics/{missing}',f'/diagnostics/{missing}/live',f'/monitoring/{missing}/runs']:
        assert c.get(P+path,headers=uh).status_code==404
    assert c.post(P+f'/notifications/{missing}/read',headers=uh).status_code==404
    assert c.patch(P+f'/work-orders/{missing}',headers=uh,json={'status':'OPEN'}).status_code==404
    for path,body in [(f'/admin/accounts/{missing}',{'active':True,'roles':['USER']}),(f'/admin/service-centers/{missing}',{}),(f'/admin/merchants/{missing}',{}),(f'/admin/products/{missing}',{'status':'REJECTED'})]:
        assert c.patch(P+path,headers=ah,json=body).status_code==404
    assert c.post(P+f'/products/{missing}/quote',headers=uh,json={}).status_code==404
    assert c.post(P+f'/staff-invitations/{missing}/accept',headers=uh).status_code==404
    for path in ['/settings','/notifications','/marketplace/products','/admin/summary','/navigation']:
        assert c.get(P+path).status_code==401


def test_schedule_disabled_missed_and_private_runs(environment):
    c,e=environment;uid,uh=register(c);other,oh=register(c,'other');vid=vehicle(c,uh)
    schedule=c.put(P+'/monitoring',headers=uh,json={'profile_id':vid,'consent':True,'cadence':'CUSTOM','custom_interval_minutes':60}).json()['id']
    with Session(e) as db:
        row=db.get(MonitoringSchedule,schedule);row.next_due=utcnow()-timedelta(days=2);db.commit()
    assert c.post(P+f'/monitoring/{schedule}/dispatch',headers=uh).json()['status']=='MISSED'
    assert c.post(P+f'/monitoring/{schedule}/dispatch',headers=oh).status_code==404
    assert c.get(P+f'/monitoring/{schedule}/runs',headers=oh).status_code==404
    c.put(P+'/monitoring',headers=uh,json={'profile_id':vid,'consent':True,'enabled':False,'cadence':'WEEKLY'})
    assert c.post(P+f'/monitoring/{schedule}/dispatch',headers=uh).status_code==403


def test_invalid_business_inputs(environment):
    c,e=environment;uid,uh=register(c);center=workshop(c,uh)
    assert c.post(P+f'/service-centers/{center}/staff-invitations',headers=uh,json={'account_id':str(uuid4()),'role':'viewer'}).status_code==404
    merchant=c.post(P+'/merchants',headers=uh,json={'name':'Shop','address':'Address'}).json()['id']
    base={'name':'Part','category':'PART','price_minor':100,'currency':'USD','stock':1}
    for changes in [{'stock':-1},{'price_minor':1.5},{'image_url':'http://example.invalid/a.png'},
                    {'compatibility':[{'make':'x','model':'x','engine':'x','year_from':2020,'year_to':2000}]}]:
        assert c.post(P+f'/merchants/{merchant}/products',headers=uh,json={**base,**changes}).status_code==422
    pid=c.post(P+f'/merchants/{merchant}/products',headers=uh,json=base).json()['id']
    for changes in [{'basis_points':10001},{'audience':'CENTER'}, {'starts_at':'2000-01-01T00:00:00'}]:
        payload={'basis_points':1000,'starts_at':utcnow().isoformat(),'ends_at':(utcnow()+timedelta(days=1)).isoformat(),**changes}
        assert c.post(P+f'/products/{pid}/offers',headers=uh,json=payload).status_code==422
    assert c.post(P+f'/products/{pid}/offers',headers=uh,json={'basis_points':1000,'audience':'CENTER','center_id':str(uuid4()),'starts_at':utcnow().isoformat(),'ends_at':(utcnow()+timedelta(days=1)).isoformat()}).status_code==404


def test_optimistic_session_update_rejects_lost_write(environment):
    from sqlalchemy.orm.exc import StaleDataError
    from ecosystem.business_models import DiagnosticRecord
    c,e=environment;uid,uh=register(c);vid=vehicle(c,uh)
    sid=c.post(P+'/diagnostics',headers=uh,json={'profile_id':vid}).json()['id']
    with Session(e) as first,Session(e) as second:
        a=first.get(DiagnosticRecord,sid);b=second.get(DiagnosticRecord,sid)
        a.payload={**a.payload,'connection_type':'first'};first.commit()
        b.payload={**b.payload,'connection_type':'lost'}
        with pytest.raises(StaleDataError):second.commit()
    assert c.get(P+f'/diagnostics/{sid}',headers=uh).json()['session']['connection_type']=='first'


def test_operator_bootstrap_is_explicit_and_first_admin_only(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    from sqlalchemy import create_engine
    from ecosystem.models import Base, Account
    engine=create_engine('sqlite:///'+str(tmp_path/'operator.sqlite'))
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Account(email='operator@example.invalid',full_name='Operator',password_hash='not-used-by-bootstrap'));db.commit()
    engine.dispose()
    root=Path(__file__).resolve().parents[2]
    env={**os.environ,'DATABASE_URL':'sqlite:///'+str(tmp_path/'operator.sqlite')}
    command=[sys.executable,str(root/'scripts/bootstrap_business_admin.py'),'--email','operator@example.invalid']
    assert subprocess.run(command,env=env,capture_output=True).returncode==2
    result=subprocess.run(command+['--grant-admin'],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'audit recorded' in result.stdout
    assert subprocess.run(command+['--grant-admin'],env=env,capture_output=True).returncode==2


def test_diagnostic_localization_is_response_only_and_french_fallback_explicit(environment):
    from ecosystem.business_models import DiagnosticRecord
    c,e=environment;uid,uh=register(c);vid=vehicle(c,uh)
    sid=c.post(P+'/diagnostics',headers=uh,json={'profile_id':vid}).json()['id']
    c.put(P+'/settings',headers=uh,json={'language':'ru'})
    result=c.post(P+f'/diagnostics/{sid}/analyze',headers=uh,json={'dtcs':['P0302']})
    assert result.status_code==200,result.text
    assert result.headers['content-language']=='ru'
    assert any('\u0400'<=char<='\u04ff' for char in result.json()['hypotheses'][0]['category'])
    with Session(e) as db:
        assert all(ord(char)<128 for char in db.get(DiagnosticRecord,sid).payload['hypotheses'][0]['category'])
    c.put(P+'/settings',headers=uh,json={'language':'fr'})
    response=c.get(P+f'/diagnostics/{sid}',headers=uh)
    assert response.headers['content-language']=='en' and response.headers['x-language-fallback']=='true'


def test_suspended_seller_is_not_published_or_quotable(environment):
    c,e,ah,sh,merchant,pid,payload=approved(environment)
    seller=c.get(P+'/me',headers=sh).json()['id']
    assert c.get(P+'/marketplace/products',headers=ah).json()
    assert c.patch(P+f'/admin/accounts/{seller}',headers=ah,json={'active':False,'roles':['USER','MARKET']}).status_code==200
    assert c.get(P+'/marketplace/products',headers=ah).json()==[]
    assert c.post(P+f'/products/{pid}/quote',headers=ah,json={}).status_code==404
