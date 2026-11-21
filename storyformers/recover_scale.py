"""Prepare explicitly accounted retries after a stopped suite's unknown outcomes.

No API calls. Original dispatches and their full budget reservations are retained.
Requires the suite lock, so it cannot race live requests or their accounting.
"""

import argparse
import fcntl
import json
from pathlib import Path

from .annotation import fingerprint
from .online_teacher import atomic_json


def prepare(root):
    with (root/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget_path=root/'budget.json'
        budget=json.loads(budget_path.read_text())
        recovered=[]
        for directory in sorted(root.glob('run_*/step_*')):
            if (directory/'decision.json').exists() or (directory/'response.json').exists():
                continue
            identifier=str(directory.relative_to(root))
            attempts=directory/'attempts'
            plans=sorted(directory.glob('uncertain_recovery_*.json'))
            pending=next((p for p in plans if not json.loads(p.read_text()).get('prepared')),None)
            if pending:
                plan=json.loads(pending.read_text());plan_path=pending
            else:
                if not attempts.exists() or not list(attempts.iterdir()):continue
                last=sorted(attempts.iterdir())[-1]
                error=json.loads((last/'error.json').read_text()) if (last/'error.json').exists() else {}
                if error.get('before_send') or (error.get('status')==429 and error.get('code')=='flex_unavailable'):
                    continue  # Normal dispatcher can resume a known free rejection.
                if error.get('type') not in ('APITimeoutError','APIConnectionError'):
                    continue  # No blind recovery of unclassified or still-running outcomes.
                entry=budget['calls'][identifier]
                assert entry['state']=='reserved'
                body=json.loads((directory/'request.json').read_text())
                assert fingerprint(body)==entry['request_sha256']
                number=len(plans)+1
                archive_id=f'{identifier}/unresolved_{number:03d}'
                archive=directory/'uncertain_attempts'/f'{number:03d}'
                plan_path=directory/f'uncertain_recovery_{number:03d}.json'
                plan=dict(original_identifier=identifier,archive_identifier=archive_id,
                    archive_directory=str(archive.relative_to(root)),original_reservation=entry,
                    request_sha256=entry['request_sha256'],prepared=False,
                    reason='Outcome unknown after transport failure. Preserve original request and full reservation; '
                           'the next identical logical-step request obtains a new separate budget reservation. '
                           'Neither provider deduplication nor absence of a charge is assumed.')
                atomic_json(plan_path,plan)
            archive_id=plan['archive_identifier'];archive=root/plan['archive_directory']
            if archive_id not in budget['calls']:
                entry=budget['calls'].pop(identifier)
                assert entry==plan['original_reservation']
                budget['calls'][archive_id]=dict(**entry,original_identifier=identifier)
                budget['calls'][archive_id]['state']='unresolved'
                atomic_json(budget_path,budget)
            # A crash between ledger move and archive rename is resumable. Until
            # the rename completes, the normal dispatcher refuses to resend.
            archive.parent.mkdir(exist_ok=True)
            if not archive.exists():attempts.rename(archive)
            plan['prepared']=True
            atomic_json(plan_path,plan)
            recovered.append(identifier)
        return recovered


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    print(json.dumps(dict(prepared_retries=prepare(args.root)),indent=2))
