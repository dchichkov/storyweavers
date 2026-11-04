"""Exhaust the untouched Sol pack's small parameter grid in local isolation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from storyscenes.authoring_api import sandbox_policy, save

CHECK = '''from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from storyscenes.mini_adventures.kite import world as w
from storyscenes.mini_adventures.review import verify_row, describe

attempts, good = [], []
for wind, gentle, frayed, mend in product(range(3), (False, True), (False, True), (False, True)):
    p = w.Parameters(wind=wind, gentle=gentle, frayed=frayed, mend=mend)
    for count in (7, 8):
        a = dict(parameters=dict(wind=wind, gentle=gentle, frayed=frayed, mend=mend), count=count)
        try:
            row = w.generate(777, count=count, params=p)
            verify_row(w, row, 777, count)
            a.update(ok=True, row=row)
            good.append(row)
        except Exception as exc:
            a.update(ok=False, error=str(exc))
        attempts.append(a)
out = dict(attempts=attempts, corpus=describe(good),
           selection="Exhaustive 24 parameter combinations at both lengths, fixed seed 777; diagnostic, not uniform judging sample")
Path('branch_audit.json').write_text(json.dumps(out, indent=2))
print(json.dumps(dict(passed=len(good), requested=len(attempts), corpus=out['corpus']), indent=2))
'''


def main():
    arm = HERE / "gpt-6.1-sol_oneshot"
    bundle = json.loads((arm / "bundle.json").read_text())
    for row in bundle["files"]:
        if (arm / "workspace" / row["path"]).read_text() != row["content"]:
            raise ValueError("Materialized pack changed")
    output = HERE / "standard_judge_v1/branch_audit.json"
    if output.exists():
        raise FileExistsError(output)
    with tempfile.TemporaryDirectory(prefix="kite-branch-audit-") as td:
        isolated = Path(td).resolve()
        work = isolated / "work"
        shutil.copytree(arm / "workspace", work)
        (work / "branch_check.py").write_text(CHECK)
        env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(isolated),
               "TMPDIR": str(isolated), "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run(["/usr/bin/sandbox-exec", "-p", sandbox_policy(isolated),
            str(Path(sys.executable).resolve()), "-I", str(work / "branch_check.py")],
            cwd=work, env=env, capture_output=True, text=True, timeout=180)
        save(output.with_name("branch_process.json"), dict(returncode=result.returncode,
             stdout=result.stdout, stderr=result.stderr))
        result.check_returncode()
        shutil.copyfile(work / "branch_audit.json", output)
        print(result.stdout)


if __name__ == "__main__":
    main()
