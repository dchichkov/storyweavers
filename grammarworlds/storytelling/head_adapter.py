"""Conservative prefix/world inputs for the new table heads.

No chosen future frame, suffix token, or rendered future sentence is consulted.
Simple prefix recognizers are adapters for this controlled grammar, not general
parsers or implementations of the 49 deferred head algorithms.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path

from ..symbolic_heads import HeadContext, HeadLibrary, ProgramRequired, Source, load_library

WEIGHTS = Path(__file__).with_name("head_weights.json")
TUNED_WEIGHTS = Path(__file__).with_name("head_weights_tuned.json")
ADAPTED_IDS = ("P001", "P002", "P007", "P013", "P023", "P059")


def _rows(mapping):
    return [{"tokens": list(key), "weight": value} for key, value in mapping.items()]


class StoryHeads:
    def __init__(self, world, *, profile="manual", strength=1.0, head_ids=None, weights_path=None):
        if profile not in {"seed", "manual", "tuned"}:
            raise ValueError("head profile must be seed, manual or tuned")
        if not math.isfinite(strength) or not 0 <= strength <= 10:
            raise ValueError("head strength must be finite and in [0, 10]")
        base = load_library()
        self.enabled = tuple(head_ids) if head_ids is not None else tuple(
            h for h in base.ids if base.describe(h)["status"] == "table")
        if len(set(self.enabled)) != len(self.enabled):
            raise ValueError("duplicate head IDs")
        for h in self.enabled:
            if base.describe(h)["status"] == "program_required":
                raise ProgramRequired(base.describe(h))
        self.profile, self.strength = profile, strength
        self.config = json.loads(Path(weights_path or (TUNED_WEIGHTS if profile == "tuned" else WEIGHTS)).read_text())
        self.weights_sha256 = hashlib.sha256(json.dumps(self.config, sort_keys=True).encode()).hexdigest()
        specs = [base.describe(h) for h in self.enabled]
        self.seed_pairs = {s["id"]: {tuple(r["tokens"]) for r in s["selection"]} for s in specs}
        if profile != "seed":
            for s in specs:
                if s["id"] == "P001":
                    for number in ("singular", "plural"):
                        s["projection"].append({"tokens": ["number:"+number, number], "weight": 1})
                        for q in ("past_be", "present_be"):
                            s["selection"].append({"tokens": [q, "number:"+number], "weight": 1})
                if s["id"] == "P023":
                    c = self.config["P023"]
                    # Replace only the live profile; original 10-example seeds stay intact.
                    s["selection"] = _rows({("action", k): 1 for k in c["source_features"]})
                    s["projection"] = _rows({(k, f): 1 for k, f in c["source_features"].items()})
                    s["receiver"] = _rows({(f, w): v for f, words in c["receiver"].items() for w, v in words.items()})
                if s["id"] == "P059":
                    cues = self.config["P059"]["receiver"]
                    queries = {"i", "me", "he", "she", "they", "we", "it"}
                    queries.update(e.noun.lower().split()[-1] for e in world.entities.values() if e.kind == "person")
                    s["receiver_mode"] = "multipliers"
                    s["selection"] = _rows({(q, cue): 1 for q in queries for cue in cues})
                    s["projection"] = _rows({(cue, cue): 1 for cue in cues})
                    s["receiver"] = _rows({(cue, w): v for cue, words in cues.items() for w, v in words.items()})
        self.library = HeadLibrary(specs)

    def metadata(self):
        return dict(profile=self.profile, strength=self.strength, head_ids=list(self.enabled),
                    adapted_ids=[h for h in self.enabled if h in ADAPTED_IDS],
                    awaiting_adapter=[h for h in self.enabled if h not in ADAPTED_IDS],
                    weights_sha256=self.weights_sha256, weights=deepcopy(self.config))

    @staticmethod
    def subject(world, prefix):
        """Resolve only a complete simple subject at the current predicate boundary.

        Multi-entity/possessive/complex subjects abstain. A visible quote's speaker
        is read from its explicit attribution. Pronouns require a unique carrier.
        """
        lower = tuple(t.lower() for t in prefix)
        quote = lower.count("“") > lower.count("”")
        if quote:
            start = max(i for i,t in enumerate(lower) if t == "“")
            local = lower[start+1:]
            if local not in {("i",), ("let", "me")}:
                return None, quote
            attribution = lower[:start]
            speakers = set()
            for id,e in world.entities.items():
                if e.kind != "person":
                    continue
                ending = tuple(e.noun.lower().split()) + ("said", ",")
                ending_present = tuple(e.noun.lower().split()) + ("says", ",")
                if attribution[-len(ending):] in (ending, ending_present):
                    speakers.add(id)
                for listener in world.entities.values():
                    if listener.kind != "person":
                        continue
                    for speech_verb in ("told", "tells"):
                        ending = tuple(e.noun.lower().split()) + (speech_verb,) + tuple(listener.noun.lower().split()) + (",",)
                        if attribution[-len(ending):] == ending:
                            speakers.add(id)
            return (next(iter(speakers)) if len(speakers) == 1 else None), quote
        boundary = max((i for i,t in enumerate(lower) if t in {".", "!", "?", ",", "and", "but", "because", "”"}), default=-1)
        local = lower[boundary+1:]
        while local and local[0] == ",":
            local = local[1:]
        names = [id for id,e in world.entities.items()
                 if local in {tuple(e.noun.lower().split()), ("the",)+tuple(e.noun.lower().split())}]
        if len(names) == 1:
            return names[0], quote
        if len(local) == 1 and local[0] in {"he", "she", "it", "they"}:
            candidates = [id for id,e in world.entities.items() if e.pronoun == local[0]]
            if len(candidates) == 1:
                return candidates[0], quote
        return None, quote

    def inputs(self, world, prefix, *, tense, available, attribute_memory=None):
        if not prefix:
            return [], []
        lower = tuple(t.lower() for t in prefix)
        scope = f"event:{len(world.history)+1}:position:{len(prefix)}"
        requests, memory = {}, []

        def add(h, query, key, source_id, confidence=1):
            if h not in self.enabled:
                return
            if h in requests and requests[h].query != query:
                return  # Ambiguous queries are not silently combined into one meaning.
            spec = self.library.describe(h)
            requests[h] = HeadContext(h, query, scope, self.strength)
            memory.append(Source(f"{h}:{source_id}", spec["input_channel"], scope, key, confidence))

        actors = defaultdict(float)
        if attribute_memory is None:
            actor, in_quote = self.subject(world, prefix)
            if actor:
                actors[actor, in_quote] = 1.
        else:
            in_quote = any(m['attributes'].get('quoted') for m in attribute_memory)
            for candidate_memory in attribute_memory:
                a = candidate_memory['attributes']
                actor = a.get('entity')
                if (a.get('syntax_role') == 'subject' and a.get('pos') in {'PRON', 'PROPN', 'NOUN'}
                        and actor in world.entities and not (a.get('nominal') or {}).get('owner')):
                    actors[actor, bool(a.get('quoted'))] += candidate_memory['probability']
        for (actor, quoted), confidence in actors.items():
            confidence = min(1., confidence)  # normalized posterior may round above one
            entity = world.entities[actor]
            origin = 'annotated_subject' if attribute_memory is not None else 'entity'
            add("P001", "present_be" if quoted or tense == "present" else "past_be",
                "number:"+entity.number if self.profile != "seed" else entity.noun.lower(),
                f"{origin}:{actor}:number", confidence)
            if self.profile != "seed" and entity.kind == "person":
                threshold = self.config["P059"]["threshold"]
                for concept, value in sorted(entity.memes.items()):
                    cue = concept + (":high" if value >= threshold else ":low")
                    if cue in self.config["P059"]["receiver"]:
                        add("P059", lower[-1], cue, f"{origin}:{actor}:memes:{concept}", confidence)
                instruments = sorted({f.instrument for _, f in available if f.actor == actor and f.instrument})
                for id in instruments:
                    if id in world.entities:
                        add("P023", "action", world.entities[id].noun.lower(),
                            f"{origin}:{actor}:guard_approved_instrument:{id}", confidence)
        if lower[-1] in {"i", "you", "he", "she", "it", "they", "we"}:
            add("P002", "present_be" if in_quote or tense == "present" else "past_be",
                "I" if lower[-1] == "i" else lower[-1], f"token:{len(prefix)-1}")

        # Exact prefix triggers from the seed contracts. They never inspect a
        # candidate suffix or infer a future speech intention from an event label.
        for h in ("P013", "P059"):
            if h == "P059" and self.profile != "seed":
                continue
            pairs = self.seed_pairs.get(h, ())
            for q,key in sorted(pairs):
                if q.lower() == lower[-1]:
                    parts = tuple(key.lower().split("_"))
                    if any(lower[i:i+len(parts)] == parts for i in range(len(lower)-len(parts))):
                        add(h, q, key, f"prefix-cue:{key}")
        if lower[-1] in {"and", "but", "or"}:
            for q,key in sorted(self.seed_pairs.get("P007", ())):
                parts = tuple(key.lower().split("_"))
                if q == lower[-1] and lower[-1-len(parts):-1] == parts:
                    add("P007", q, key, f"prefix:{len(prefix)-1-len(parts)}")

        # These heads require structural/intent inputs absent from the current
        # adapter. Do not manufacture activation merely to increase head counts.
        return list(requests.values()), memory

    def predict(self, forest, prefix, world, *, tense, available):
        prediction = deepcopy(forest.predict(prefix))
        contexts, memory = self.inputs(world, prefix, tense=tense, available=available,
                                      attribute_memory=forest.attribute_memory() if hasattr(forest, "attribute_memory") else None)
        base = {c["word"]: c["probability"] for c in prediction["choices"]}
        # Agreement features should distinguish competing agreement forms, not
        # prefer a copular construction over another already grammatical verb.
        agreement_forms = {"am", "is", "are", "was", "were"} & set(base)
        gated = set()
        if len(agreement_forms) < 2:
            gated = {c.head_id for c in contexts if c.head_id in {"P001", "P002"}}
            contexts = [replace(c, strength=0) if c.head_id in gated else c for c in contexts]
        result = self.library.rerank(base, contexts, memory)
        for h in result["heads"]:
            if h["head_id"] in gated:
                h["receiver_gate"] = "no_competing_agreement_forms"
        tv = .5 * sum(abs(result["probabilities"][w]-p) for w,p in result["base"].items())
        for c in prediction["choices"]:
            c["grammar_probability"] = c["probability"]
            if tv > 1e-12:
                c["probability"] = result["probabilities"][c["word"]]
        # Keep original candidate order: matched-seed differences must be caused
        # by probability changes, not sorting roundoff or consuming extra RNG.
        prediction["symbolic_heads"] = result["heads"]
        prediction["head_total_variation"] = tv
        prediction["grammar_prefix_probability"] = prediction.pop("prefix_probability")
        return prediction
