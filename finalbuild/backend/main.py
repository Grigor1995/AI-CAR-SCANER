"""Independent shared backend product: python -m backend.main --migrate."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys


def main(argv=None):
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
    for directory in (root,root/'backend'):
        if str(directory) not in sys.path:sys.path.insert(0,str(directory))
    from shared.environment import apply_environment
    apply_environment()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,help='Explicit persistent SQLite file; otherwise preserve DATABASE_URL or use the backend app-data directory')
    parser.add_argument('--migrate',action='store_true',help='Apply reviewed additive Alembic migrations before serving')
    parser.add_argument('--host',default=os.environ.get('AI_CAR_BACKEND_HOST','127.0.0.1'))
    parser.add_argument('--port',type=int,default=int(os.environ.get('AI_CAR_BACKEND_PORT','8001')))
    parser.add_argument('--local-ai',action='store_true',help='Start an existing configured local llama-server/model, without downloading files')
    parser.add_argument('--check',action='store_true',help='Check centralized imports without starting services or creating a database')
    args=parser.parse_args(argv)
    if not 1<=args.port<=65535:parser.error('port must be in 1..65535')
    if args.check:
        import vehicle.obd.client
        print('Shared backend ready; vehicle core: '+str(vehicle.obd.client.__file__));return 0
    os.environ.update(AI_CAR_ECOSYSTEM_ENABLED='1',AI_CAR_BACKEND_HOST=args.host,AI_CAR_BACKEND_PORT=str(args.port))
    if args.database is not None or not os.environ.get('DATABASE_URL'):
        storage=Path(os.environ.get('APPDATA') or os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'AI-Car-Backend'
        path=(args.database or storage/'business.sqlite').expanduser().resolve()
        path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not path.exists():path.touch(mode=0o600,exist_ok=False)
        os.environ['DATABASE_URL']='sqlite:///'+path.as_posix()
    if args.migrate:
        from alembic import command
        from alembic.config import Config
        command.upgrade(Config(str(root/'backend/alembic.ini')),'head')
    runtime=None
    try:
        if args.local_ai:
            os.environ.update(LLM_PROVIDER='llama-server',LLM_ENABLED='1',AI_CAR_DISABLE_LLM_AUTOSTART='0')
            from backend import desktop_runtime as runtime
            os.environ['LOCAL_LLM_SERVER_MODEL']=str(runtime._resolve_model_path())
            runtime.start_llama_server(wait_for_ready=False)
        from backend.server import main as serve
        serve()
    finally:
        if runtime is not None:runtime.stop_llama_server()
    return 0

if __name__=='__main__':raise SystemExit(main())
