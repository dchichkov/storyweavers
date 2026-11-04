"""Worker for isolated, unfiltered checks of one authored pack."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import traceback

# Invoked with python -I inside a copied sandbox; no host repository imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grammarworlds.pack_runtime import sample, replay


def main():
    spec = importlib.util.spec_from_file_location("authored_pack", Path("pack.py").resolve())
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    attempts, interventions = [], []
    try:
        spec.loader.exec_module(module)
    except Exception:
        Path("check.json").write_text(json.dumps(dict(import_ok=False, error=traceback.format_exc(), attempts=[])))
        return
    for seed in range(1000, 1060):
        record = dict(seed=seed, ok=False)
        try:
            row = sample(module, seed)
            replay(module, row)
            if seed == 1000:
                assert row == sample(module, seed), "generation is not reproducible"
                Path("word_trace.json").write_text(json.dumps(row["word_trace"], indent=2))
            del row["word_trace"]
            record.update(ok=True, row=row)
        except Exception:
            record["error"] = traceback.format_exc()
        attempts.append(record)
    for willing in (False, True):
        for seed in range(2000, 2010):
            record = dict(seed=seed, partner_willing=willing, ok=False)
            try:
                row = sample(module, seed, partner_willing=willing, interventions=True)
                record.update(ok=True, joined=row["joined"], guard_checks=row["guard_interventions"],
                              story=row["story"], frames=row["frames"])
            except Exception:
                record["error"] = traceback.format_exc()
            interventions.append(record)
    rows = [r["row"] for r in attempts if r["ok"]]
    counts = Counter(" > ".join(f["kind"] for f in r["frames"]) for r in rows)
    errors = Counter(r["error"].strip().splitlines()[-1] for r in attempts + interventions if not r["ok"])
    result = dict(import_ok=True, requested=60, passed=len(rows),
        intervention_requested=len(interventions), intervention_passed=sum(r["ok"] for r in interventions),
        forced_willing_duets=sum(r.get("joined", False) for r in interventions if r["partner_willing"]),
        forced_unwilling_duets=sum(r.get("joined", False) for r in interventions if not r["partner_willing"]),
        failures=dict(errors), attempts=attempts, interventions=interventions,
        corpus=dict(unique_texts=len({r["story"] for r in rows}), unique_event_paths=len(counts),
            event_paths=dict(counts), outcomes=dict(Counter("private_duet" if r["joined"] else "solo" for r in rows)),
            mean_words=statistics.mean(r["word_count"] for r in rows) if rows else None,
            mean_events=statistics.mean(r["event_count"] for r in rows) if rows else None,
            branching_word_steps=sum(r["branching_steps"] for r in rows),
            total_word_steps=sum(r["prediction_steps"] for r in rows)))
    Path("check.json").write_text(json.dumps(result, indent=2))
    Path("samples.md").write_text("# Unfiltered sample positions\n\n" + "\n\n".join(
        f"## Seed {r['seed']}\n\n{r['row']['story'] if r['ok'] else r['error']}" for r in attempts))
    print(json.dumps({k: v for k, v in result.items() if k not in ("attempts", "interventions")}, indent=2))


if __name__ == "__main__":
    main()
