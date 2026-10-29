"""Explicit local operator bootstrap; no public registration privilege escalation."""
import argparse
import os
from pathlib import Path
import sys
from sqlalchemy import select
from sqlalchemy.orm import Session
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from diagnostic.database import database_engine
from ecosystem.models import Account,AccountRole,AuditEvent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--email',required=True);parser.add_argument('--grant-admin',required=True,action='store_true');args=parser.parse_args()
    if not os.environ.get('DATABASE_URL'):parser.error('Set explicit DATABASE_URL to the migrated database')
    engine=database_engine(os.environ['DATABASE_URL'])
    try:
        with Session(engine) as db:
            account=db.scalar(select(Account).where(Account.email==args.email.casefold(),Account.active.is_(True)))
            if account is None:parser.error('Register the active account first')
            if db.scalar(select(AccountRole.account_id).where(AccountRole.role=='ADMIN')):parser.error('An ADMIN already exists; use audited admin APIs instead')
            db.add(AccountRole(account_id=account.id,role='ADMIN'));db.add(AuditEvent(actor_id=account.id,action='OPERATOR_ADMIN_BOOTSTRAP',target_id=account.id));db.commit()
            print('ADMIN granted to the explicitly selected existing account; audit recorded.')
    finally:engine.dispose()

if __name__=='__main__':main()
