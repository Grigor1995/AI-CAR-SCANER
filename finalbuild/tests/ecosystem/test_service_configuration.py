"""Real gateway account authorization and durable configuration audit."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_foundation import register, P
from ecosystem.models import AccountRole, AuditEvent
from ecosystem import config_api
from configuration import ConfigManager

def test_configuration_admin_boundary_revision_audit_and_catalog_access(environment, tmp_path, monkeypatch):
    client, engine=environment
    (tmp_path/'config').mkdir();(tmp_path/'config/global_config.json').write_text('{}')
    manager=ConfigManager(tmp_path,environ={})
    monkeypatch.setattr(config_api,'get_manager',lambda:manager)
    account,headers=register(client,'config-user')
    assert client.get(P+'/catalog/makes').status_code==401
    assert client.get(P+'/catalog/makes?q=BMW',headers=headers).json()==['BMW']
    response=client.get(P+'/catalog/profile?make=BMW&model=3%20Series&year=2013',headers=headers)
    assert response.status_code==200,response.text
    portrait=response.json()['image']['portrait_api_url']
    assert portrait.startswith(P+'/catalog/portrait?')
    assert client.get(portrait).status_code==401
    assert client.get(portrait,headers=headers).status_code==200
    assert client.get(P+'/configuration',headers=headers).status_code==403
    patch={'expected_revision':1,'changes':{'services.vehicle_catalog.retries':2}}
    assert client.patch(P+'/configuration',headers=headers,json=patch).status_code==403
    assert manager.revision==1
    with Session(engine) as db:db.add(AccountRole(account_id=account,role='ADMIN'));db.commit()
    response=client.patch(P+'/configuration',headers=headers,json=patch)
    assert response.status_code==200,response.text
    assert response.json()['revision']==2 and manager.snapshot.services.vehicle_catalog.retries==2
    assert client.patch(P+'/configuration',headers=headers,json=patch).status_code==409
    assert client.patch(P+'/configuration',headers=headers,json={'expected_revision':2,'changes':{'marketplace.payments_enabled':1}}).status_code==409
    with Session(engine) as db:
        events=db.scalars(select(AuditEvent).where(AuditEvent.action=='CONFIG_RUNTIME_CHANGED')).all()
        assert len(events)==1
    assert 'model_path' not in client.get(P+'/configuration',headers=headers).text
