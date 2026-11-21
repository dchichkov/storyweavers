"""Supervise the fixed ten-run experiment, recovering only stopped API failures."""

import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .online_teacher import atomic_json
from .recover_scale import prepare


def live_experiment(pid,root):
    result=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
    if result.stderr.strip():
        raise RuntimeError('Process observation failed; do not assume it exited: '+result.stderr.strip())
    return result.returncode==0 and 'storyformers.online_scale' in result.stdout and root.name in result.stdout


def pending_runs(root,manifest):
    return [r['name'] for r in manifest['runs']
            if any(not (root/r['name']/f'step_{i:03d}/decision.json').exists() for i in range(10))]


def supervise(root,wait_pid=None):
    root=root.resolve()
    manifest=json.loads((root/'manifest.json').read_text())
    def status(phase,**extra):
        atomic_json(root/'supervisor.json',dict(phase=phase,pid=os.getpid(),
            updated_at=datetime.now(timezone.utc).isoformat(),**extra))
    if wait_pid:
        print(f'Observing existing experiment PID {wait_pid}; no restart while it is live.',flush=True)
        while live_experiment(wait_pid,root):
            status('waiting_for_existing_process',experiment_pid=wait_pid,
                   committed_iterations=len(list(root.glob('run_*/step_*/decision.json'))))
            time.sleep(15)
    for cycle in range(20):
        if (root/'completed.json').exists():break
        remaining=pending_runs(root,manifest)
        failures=[]
        for name in remaining:
            path=root/name/'failure.json'
            if path.exists():
                failure=json.loads(path.read_text())
                if failure['type'] not in ('APITimeoutError','APIConnectionError','RateLimitError'):
                    failures.append(f'{name}: {failure["type"]}: {failure["message"]}')
        if failures:
            status('needs_inspection',failures=failures)
            raise RuntimeError('; '.join(failures))
        # Acquires the suite lock and retains full reservations for unknown
        # outcomes. A live competing owner makes this fail instead of racing it.
        recovered=prepare(root) if remaining else []
        command=[sys.executable,'-m','storyformers.online_scale','--out',str(root),
                 '--concurrency',str(manifest['concurrency'])]
        if not remaining:command.append('--evaluate-only')
        print(f'Resume cycle {cycle+1}: {len(remaining)} unfinished runs; {len(recovered)} separately budgeted retries.',flush=True)
        child=subprocess.Popen(command)
        status('running',cycle=cycle+1,experiment_pid=child.pid,recovered=recovered)
        code=child.wait()  # Terminal child status, never an observation timeout.
        status('child_exited',cycle=cycle+1,exit_code=code)
        if code==0 and (root/'completed.json').exists():break
        if not pending_runs(root,manifest) and code!=0:
            status('needs_inspection',reason='All decisions exist, but evaluation failed.')
            raise RuntimeError('Inspect evaluation failure before retrying.')
    else:
        status('needs_inspection',reason='Twenty recovery cycles exhausted.')
        raise RuntimeError('Recovery-cycle limit reached; inspect retained journals.')
    status('auditing')
    subprocess.run([sys.executable,'-m','storyformers.scale_report',str(root)],check=True)
    status('complete')
    print('Completion audit passed for all ten runs and 100 iterations.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--wait-pid',type=int)
    args=parser.parse_args()
    with (args.out/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        supervise(args.out,args.wait_pid)
