"""Save reproducible, unfiltered generations from a trained grammar checkpoint."""

import argparse
import json
from pathlib import Path

from .neuron_review import model_fingerprint
from .transformer import Storyformer


ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / "runs/learning_emulation_20261109/replay/final_model.json"


def sample(checkpoint=CHECKPOINT):
    model = Storyformer.load(checkpoint)
    cases = [(None, seed, [], 20) for seed in range(12)]
    for verb in ("ate", "used"):
        prompt = [dict(token="Lily", pos="pn"), dict(token=verb, pos="v")]
        cases.extend((f"Lily {verb}", seed, prompt, 16) for seed in range(3))
    samples = []
    for prompt_text, seed, context, steps in cases:
        records = model.generate(context, steps, seed=seed)
        tokens = [row["token"] for row in records]
        text = " ".join(token for token in tokens if token != "<END>").replace(" .", ".")
        samples.append(dict(prompt=prompt_text, seed=seed, max_new_tokens=steps, tokens=tokens,
                            text=text, ended=tokens[-1] == "<END>", records=records))
    return dict(model_sha256=model_fingerprint(model),
                policy="Unprompted seeds 0–11; prompted seeds 0–2 for each prompt. No rejection or filtering.",
                decoding="Sample the retained top-ten token/bundle distribution, renormalized by retained mass.",
                display="Only END markers and spaces before periods are removed from display text; raw tokens are retained.",
                samples=samples)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = sample(args.checkpoint)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    for row in report["samples"]:
        print(f"{row['prompt'] or '<empty>'} / seed {row['seed']}: {row['text']}")


if __name__ == "__main__":
    main()
