from pathlib import Path
import json
from grammarworlds.storytelling.runtime import SCENARIOS,generate,replay
from grammarworlds.storytelling.qa import questions
base=Path("/Users/dmitry/storyweavers/grammarworlds/runs/luna_short_dialogue_qa_20261103")
out=Path("../baseline_heldout_stories.jsonl")
matched=0
for scenario in SCENARIOS:
    for old in json.loads((base/scenario/"pool.json").read_text()):
        row=generate(scenario,old["seed"])
        assert row["story"]==old["story"]
        assert questions(row)==old["qa"]
        matched+=1
with out.open("w") as sink:
    for scenario in SCENARIOS:
        for tense in ("past","present"):
            for seed in range(1000,1060):
                row=generate(scenario,seed,tense=tense);replay(row)
                sink.write(json.dumps(dict(scenario=scenario,seed=seed,tense=tense,story=row["story"],qa=questions(row),frames=[e["frame"] for e in row["final_world"]["history"]]))+"\n")
        print(scenario,flush=True)
Path("../baseline_regeneration.json").write_text(json.dumps(dict(matched_original_stories_and_qa=matched,heldout_stories=840),indent=2))
