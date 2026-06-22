#!/usr/bin/env python3
"""
conceptnet_mine.py - grow a story-grounded ConceptNet from TinyStories.

Mirrors `kernel.py`: an async, few-shot LLM pass over the TinyStories corpus,
streaming JSONL out. Where `kernel.py` extracts the *narrative kernel*, this
extracts the *commonsense substrate* the kernel type system needs -- the
`kind_of` / `role_action` / `Causes` / `MotivatedByGoal` edges that ConceptNet
either lacks for this domain or mis-levels (see the README "Bootstrap" section:
ostrich's missing neck, the empty `cautionary tale`). Mining the assertions from
the corpus we actually model makes coverage match usage by construction and
keeps the senses the *story* senses.

    TinyStories  ==  Open Mind Common Sense corpus
    this LLM pass ==  the assertion parser

Three modes (LLM only in `extract`, mirroring "LLMs at synthesis time, never at
runtime"):

    extract    story  -> dataXX.assertions.jsonl   (raw, grounded, weight=salience)
    rdf        jsonl  -> dataXX.assertions.nq       (N-Quads; named graph = story = provenance)
    aggregate  jsonl  -> conceptnet_ts.hf.jsonl     (collapsed + weighted, 6-field lossless RDF rows)

The 6-field rows match the CleverThis/conceptnet HuggingFace schema, so the
mined edges merge with an imported ConceptNet 5.7 dump and round-trip to Turtle
via the dataset's own `convert_to_rdf`. URIs follow ConceptNet conventions
(`http://conceptnet.io/c/en/<lemma>`, `/r/<Relation>`); narrative-specific
relations live under a small local namespace.

Usage (use the repo venv):

    ./.venv/bin/python conceptnet_mine.py extract   --datasets 3
    ./.venv/bin/python conceptnet_mine.py rdf        data03.assertions.jsonl
    ./.venv/bin/python conceptnet_mine.py aggregate  data*.assertions.jsonl --min-weight 2
"""
from __future__ import annotations

import argparse
import asyncio
import glob
import hashlib
import json
import os
import re

# ---------------------------------------------------------------------------
# Controlled relation vocabulary -> URIs.
#
# Restricting the LLM to this set is what turns free-text into mergeable RDF.
# Most map straight onto real ConceptNet relations (so the output unions cleanly
# with an imported dump); the few narrative/affective ones ConceptNet lacks live
# under the local `tsr:` namespace.
# ---------------------------------------------------------------------------
CN_C = "http://conceptnet.io/c/en/"          # concept nodes
CN_R = "http://conceptnet.io/r/"             # ConceptNet relations
TS_R = "http://storyweavers.org/r/"          # narrative-specific relations
TS_A = "http://storyweavers.org/a/"          # reified edge (assertion) resources
TS_S = "http://storyweavers.org/story/"      # provenance: one named graph per story
TS_V = "http://storyweavers.org/voc#"        # our vocabulary terms (weight, dataset)
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XSD = "http://www.w3.org/2001/XMLSchema#"
PROV = "http://www.w3.org/ns/prov#"

# token the model may emit -> full relation URI
RELATIONS: dict[str, str] = {
    # taxonomy / structure (ConceptNet)
    "IsA": CN_R + "IsA",
    "PartOf": CN_R + "PartOf",
    "HasA": CN_R + "HasA",
    "MadeOf": CN_R + "MadeOf",
    "HasProperty": CN_R + "HasProperty",
    "DefinedAs": CN_R + "DefinedAs",
    # function / use (ConceptNet)
    "UsedFor": CN_R + "UsedFor",
    "CapableOf": CN_R + "CapableOf",
    "AtLocation": CN_R + "AtLocation",
    "LocatedNear": CN_R + "LocatedNear",
    "ReceivesAction": CN_R + "ReceivesAction",
    "HasPrerequisite": CN_R + "HasPrerequisite",
    "HasSubevent": CN_R + "HasSubevent",
    # affect / motivation -- the part the story corpus is rich in (ConceptNet)
    "Causes": CN_R + "Causes",
    "CausesDesire": CN_R + "CausesDesire",
    "Desires": CN_R + "Desires",
    "MotivatedByGoal": CN_R + "MotivatedByGoal",
    # narrative-specific (local extensions ConceptNet doesn't carry)
    "CharacterRole": TS_R + "CharacterRole",   # an instance plays a role: brother, mentor
    "FeelsToward": TS_R + "FeelsToward",        # X feels <emotion> toward Y
    "ResolvesBy": TS_R + "ResolvesBy",          # tension <problem> resolved by <move>
}

# ---------------------------------------------------------------------------
# Few-shot: one richly-grounded exemplar (the Sara/Ben park story). The target
# assertions deliberately mix easy content edges (oak_tree CapableOf be_climbed)
# with the affective/causal edges that are the real prize, and every row carries
# an `evidence` span so extraction stays grounded rather than world-knowledge.
# ---------------------------------------------------------------------------
FEWSHOT = [{
    "words": ["quit", "oak", "gloomy"],
    "features": ["Dialogue"],
    "summary": ("Sara and Ben were playing in the park, but Sara wanted to go "
                "home because it was cold and dark. Ben wanted her to stay, "
                "then saw that she was cold and unhappy, and agreed to go home."),
    "story": (
        "Sara and Ben were playing in the park. They liked to climb the big oak tree and pretend they were birds.\n"
        "But today, the sky was gloomy and the wind was cold. Sara felt sad and cold. She wanted to go home and have some hot cocoa.\n"
        '"Ben, I want to quit," she said. "It\'s too cold and dark. Let\'s go home."\n'
        "Ben liked the oak tree and wanted to stay and play.\n"
        "Ben saw that Sara was shivering and looked unhappy. He loved his sister and didn't want her to be sad. He nodded and smiled.\n"
        '"Okay, Sara, let\'s go home," he said. "We can have some hot cocoa."\n'
        "They climbed down the oak tree and ran to their home."
    ),
    "assertions": [
        {"evidence": "the big oak tree", "subject": "oak tree", "relation": "IsA", "object": "tree"},
        {"evidence": "playing in the park ... the big oak tree", "subject": "oak tree", "relation": "AtLocation", "object": "park"},
        {"evidence": "They liked to climb the big oak tree", "subject": "oak tree", "relation": "CapableOf", "object": "be climbed"},
        {"evidence": "playing in the park", "subject": "park", "relation": "UsedFor", "object": "play"},
        {"evidence": "the sky was gloomy ... Sara felt sad", "subject": "gloomy sky", "relation": "Causes", "object": "feel sad"},
        {"evidence": "It's too cold and dark. Let's go home", "subject": "feeling cold", "relation": "CausesDesire", "object": "go home"},
        {"evidence": "the wind was cold. Sara felt sad and cold", "subject": "cold weather", "relation": "Causes", "object": "feel cold"},
        {"evidence": "Ben, I want to quit", "subject": "quit", "relation": "IsA", "object": "give up"},
        {"evidence": "It's too cold and dark. Let's go home ... have some hot cocoa", "subject": "hot cocoa", "relation": "UsedFor", "object": "warm up"},
        {"evidence": "Ben saw that Sara was shivering ... He nodded", "subject": "see someone shiver", "relation": "Causes", "object": "feel sympathy"},
        {"evidence": "He loved his sister and didn't want her to be sad", "subject": "comfort sibling", "relation": "MotivatedByGoal", "object": "help a sibling"},
        {"evidence": "He loved his sister", "subject": "Ben", "relation": "CharacterRole", "object": "brother"},
        {"evidence": "It's too cold ... have some hot cocoa", "subject": "feeling cold", "relation": "ResolvesBy", "object": "hot cocoa"},
    ],
}]


def build_prompt(record: dict) -> str:
    ex = FEWSHOT[0]
    return f"""# Commonsense Assertion Extraction

You extract grounded commonsense assertions from a children's story, in the
style of ConceptNet. Output ONLY a JSON array (no prose, no code fences).

Each assertion is an object:
  {{"subject": <concept>, "relation": <REL>, "object": <concept>,
    "evidence": <short verbatim span from the story>, "salience": 1..3}}

Rules:
- `relation` MUST be one of: {", ".join(RELATIONS)}.
- subject/object are SHORT, GENERAL, REUSABLE concepts (lemmatized noun or verb
  phrases: "oak tree", "go home", "feel sad", "hot cocoa"), NOT sentences and
  NOT character names. They must be generic enough to recur across many stories
  (so the same edge can be corroborated); "wanting to quit because of cold" is
  too specific -- use "cold weather" -> "hot cocoa" instead. EXCEPT for
  CharacterRole, whose subject is the character (e.g. "Ben" -> "brother").
- Every assertion MUST be supported by an `evidence` span actually in the story.
  Do not add outside world knowledge the text does not entail.
- Prefer the affective / causal / motivational edges (Causes, CausesDesire,
  MotivatedByGoal, ResolvesBy) -- those are the commonsense a story teaches and
  that generic encyclopedias lack. Still include obvious content edges (IsA,
  AtLocation, CapableOf, UsedFor) when present.
- `salience`: 3 = central to the story, 1 = incidental.

## Example

Words: {", ".join(ex["words"])}
Features: {", ".join(ex["features"])}
Summary: {ex["summary"]}
Story:
{ex["story"]}

Assertions:
{json.dumps(ex["assertions"], indent=1)}

## Your turn

Words: {", ".join(record.get("instruction", {}).get("words", []))}
Features: {", ".join(record.get("instruction", {}).get("features", []))}
Summary: {record.get("summary", "")}
Story:
{record.get("story", "")}

Assertions:"""


def _parse_json_array(text: str) -> list[dict]:
    """Best-effort: pull the first top-level JSON array out of the completion."""
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        out = json.loads(text[start:end + 1])
        return out if isinstance(out, list) else []
    except json.JSONDecodeError:
        return []


async def extract_assertions(client, model, record: dict) -> list[dict]:
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": build_prompt(record)}],
        temperature=0.0,
        max_tokens=1200,
    )
    raw = _parse_json_array(resp.choices[0].message.content)
    # keep only well-formed rows with an allowed relation and an evidence span
    clean = []
    for a in raw:
        if not isinstance(a, dict):
            continue
        if a.get("relation") not in RELATIONS:
            continue
        if not (a.get("subject") and a.get("object") and a.get("evidence")):
            continue
        a["salience"] = int(a.get("salience", 1) or 1)
        clean.append(a)
    return clean


async def process_dataset(dataset: str) -> None:
    """Mirror kernel.py: bounded-concurrency async pass, streaming JSONL out."""
    from openai import AsyncOpenAI
    from tqdm.asyncio import tqdm

    base_url = os.environ.get("LOCALHOST_BASE_URL", "http://localhost:8001/v1")
    api_key = os.environ.get("LOCALHOST_API_KEY", "dummy-key")
    model = os.environ.get("MINE_MODEL", "gpt-oss-120b")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    sem = asyncio.Semaphore(int(os.environ.get("MINE_CONCURRENCY", "32")))

    with open(f"TinyStories_all_data/{dataset}.json") as f:
        stories = json.load(f)

    async def limited(idx: int, record: dict) -> dict:
        async with sem:
            assertions = await extract_assertions(client, model, record)
        return {
            "story_id": f"{dataset}:{idx}",
            "words": record.get("instruction", {}).get("words", []),
            "features": record.get("instruction", {}).get("features", []),
            "assertions": assertions,
        }

    async with client:
        tasks = [limited(i, r) for i, r in enumerate(stories)]
        with open(f"{dataset}.assertions.jsonl", "w") as out:
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks),
                             desc=f"Mining {dataset}"):
                out.write(json.dumps(await task) + "\n")
                out.flush()


# ---------------------------------------------------------------------------
# Term normalization + URI helpers (ConceptNet conventions).
# ---------------------------------------------------------------------------
def normalize_term(text: str) -> str:
    """'the big Oak Tree' -> 'oak_tree' (ConceptNet /c/en/<lemma> style)."""
    text = text.strip().lower()
    text = re.sub(r"^(a|an|the|some|to|be)\s+", "", text)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "_"


def concept_uri(text: str) -> str:
    return CN_C + normalize_term(text)


def rel_uri(rel: str) -> str:
    return RELATIONS[rel]


def story_uri(story_id: str) -> str:
    return TS_S + story_id.replace(":", "_")


def edge_uri(s: str, r: str, o: str) -> str:
    key = f"{normalize_term(s)}|{r}|{normalize_term(o)}"
    return TS_A + hashlib.sha1(key.encode()).hexdigest()[:16]


def _iter_assertions(paths: list[str]):
    for path in paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


# ---------------------------------------------------------------------------
# rdf mode: raw layer as N-Quads. The named graph IS the provenance -- one graph
# per story -- so weight emerges later from counting quads across graphs. Pure
# stdlib string serialization; no rdflib needed for N-Quads/N-Triples.
# ---------------------------------------------------------------------------
def _nt_uri(u: str) -> str:
    return f"<{u}>"


def write_nquads(paths: list[str], out_path: str) -> int:
    n = 0
    with open(out_path, "w") as out:
        for rec in _iter_assertions(paths):
            g = _nt_uri(story_uri(rec["story_id"]))
            for a in rec.get("assertions", []):
                s = _nt_uri(concept_uri(a["subject"]))
                p = _nt_uri(rel_uri(a["relation"]))
                o = _nt_uri(concept_uri(a["object"]))
                out.write(f"{s} {p} {o} {g} .\n")
                n += 1
    print(f"wrote {n} quads to {out_path}")
    return n


# ---------------------------------------------------------------------------
# aggregate mode: collapse (subject, relation, object) across the whole corpus.
# weight = number of distinct stories asserting the edge (this is the trust
# mechanism: one story is a guess, many are a fact; one-offs fall below
# --min-weight). Emits the 6-field lossless HF rows the CleverThis/conceptnet
# dataset uses, so the mined KB unions with an imported ConceptNet dump and
# round-trips to Turtle. Each edge is reified so weight + provenance survive.
# ---------------------------------------------------------------------------
def hf_row(subject, predicate, obj, object_type="uri",
           datatype=None, language=None) -> dict:
    return {
        "subject": subject, "predicate": predicate, "object": obj,
        "object_type": object_type, "object_datatype": datatype,
        "object_language": language,
    }


def aggregate(paths: list[str], out_path: str, min_weight: int) -> None:
    edges: dict[tuple, dict] = {}
    for rec in _iter_assertions(paths):
        sid = rec["story_id"]
        for a in rec.get("assertions", []):
            key = (normalize_term(a["subject"]), a["relation"],
                   normalize_term(a["object"]))
            e = edges.setdefault(key, {"stories": set(), "salience": 0})
            e["stories"].add(sid)
            e["salience"] += a["salience"]

    kept = {k: v for k, v in edges.items()
            if len(v["stories"]) >= min_weight}
    rows = 0
    with open(out_path, "w") as out:
        for (s, r, o), v in sorted(kept.items(),
                                   key=lambda kv: -len(kv[1]["stories"])):
            s_uri, p_uri, o_uri = CN_C + s, RELATIONS[r], CN_C + o
            a_uri = edge_uri(s, r, o)
            weight = float(len(v["stories"]))
            triples = [
                # the plain, queryable triple
                hf_row(s_uri, p_uri, o_uri),
                # ConceptNet-style reified edge carrying weight + provenance
                hf_row(a_uri, RDF + "type", TS_V + "Edge"),
                hf_row(a_uri, RDF + "subject", s_uri),
                hf_row(a_uri, RDF + "predicate", p_uri),
                hf_row(a_uri, RDF + "object", o_uri),
                hf_row(a_uri, TS_V + "weight", repr(weight),
                       "literal", XSD + "float"),
                hf_row(a_uri, TS_V + "dataset", "/d/tinystories", "literal"),
            ] + [hf_row(a_uri, PROV + "wasDerivedFrom", story_uri(sid))
                 for sid in sorted(v["stories"])]
            for t in triples:
                out.write(json.dumps(t, ensure_ascii=False) + "\n")
                rows += 1
    print(f"kept {len(kept)}/{len(edges)} edges (min_weight={min_weight}); "
          f"wrote {rows} rows to {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    pe = sub.add_parser("extract", help="LLM pass: stories -> assertions.jsonl")
    pe.add_argument("--datasets", nargs="+", type=int, default=[3],
                    help="dataXX indices to process (default: 3)")

    pr = sub.add_parser("rdf", help="assertions.jsonl -> N-Quads (provenance graphs)")
    pr.add_argument("inputs", nargs="+")
    pr.add_argument("--out", default="assertions.nq")

    pa = sub.add_parser("aggregate", help="assertions.jsonl -> weighted 6-field RDF rows")
    pa.add_argument("inputs", nargs="+")
    pa.add_argument("--out", default="conceptnet_ts.hf.jsonl")
    pa.add_argument("--min-weight", type=int, default=2,
                    help="drop edges asserted by fewer than N stories")

    args = ap.parse_args()
    if args.mode == "extract":
        for i in args.datasets:
            asyncio.run(process_dataset(f"data{i:02d}"))
    elif args.mode == "rdf":
        paths = [p for g in args.inputs for p in glob.glob(g)]
        write_nquads(paths, args.out)
    elif args.mode == "aggregate":
        paths = [p for g in args.inputs for p in glob.glob(g)]
        aggregate(paths, args.out, args.min_weight)


if __name__ == "__main__":
    main()
