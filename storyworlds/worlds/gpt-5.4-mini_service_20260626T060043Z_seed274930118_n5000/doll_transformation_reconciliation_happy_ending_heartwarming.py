#!/usr/bin/env python3
"""
storyworlds/worlds/doll_transformation_reconciliation_happy_ending_heartwarming.py
===================================================================================

A small heartwarming story world about a doll, a transformation, and a gentle
reconciliation that ends in a happy, cozy image.

Premise seed:
- A child loves a doll that feels a little plain or a little broken.
- The child wants to transform the doll into something special.
- A small disagreement or accident creates hurt feelings.
- A caring repair and shared decorating moment brings everyone back together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTINGS = {
    "bedroom": "the bedroom",
    "playroom": "the playroom",
    "nursery": "the nursery",
}

CHILD_NAMES = ["Mia", "Nora", "Lily", "Ava", "Ruby", "June", "Ella", "Zoe"]
SIBLING_NAMES = ["Ben", "Noah", "Theo", "Finn", "Leo", "Max"]
PARENT_NAMES = ["Mom", "Dad"]

TRAITS = ["gentle", "curious", "patient", "brave", "kind", "cheerful"]

DOLL_STATES = {
    "plain": "plain",
    "torn": "a little torn",
    "dull": "dull and dusty",
}

DECOR_KINDS = {
    "ribbon": {"sparkly", "soft"},
    "patch": {"soft", "cozy"},
    "paint": {"bright", "colorful"},
    "dress": {"pretty"},
}

TRANSFORMATIONS = {
    "ribbon": "tie a ribbon around the doll's hair",
    "patch": "sew a tiny patch on the doll's dress",
    "paint": "paint little flowers on the doll's shoes",
    "dress": "give the doll a pretty new dress",
}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    doll: object | None = None
    parent: object | None = None
    sibling: object | None = None
    def __post_init__(self):
        for k in ("clean", "torn", "sad", "joy", "love", "hurt", "reconcile", "pride"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    sibling_name: str
    parent_name: str
    doll_state: str
    decor: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    params: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


ASP_RULES = r"""
child_story(S) :- setting(S).
happy_ending(S) :- child_story(S), transformation(S), reconciliation(S).
valid_setting(S) :- setting(S).
valid_decor(D) :- decor(D).
valid_story(S,D) :- valid_setting(S), valid_decor(D).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for d in DECOR_KINDS:
        lines.append(asp.fact("decor", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((s, d) for s in SETTINGS for d in DECOR_KINDS)
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------


def _rule_smudge(world: World) -> list[str]:
    out = []
    child = next(e for e in world.entities.values() if e.kind == "child")
    doll = world.get("doll")
    if child.meters["messy"] >= THRESHOLD and doll.meters["clean"] >= THRESHOLD:
        sig = ("smudge",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        doll.meters["clean"] = max(0.0, doll.meters["clean"] - 1)
        doll.meters["torn"] += 0.5
        out.append(f"The doll got a little smudged during the busy moment.")
    return out


def _rule_repair(world: World) -> list[str]:
    out = []
    doll = world.get("doll")
    if doll.meters["torn"] >= THRESHOLD:
        sig = ("repair",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        doll.meters["torn"] = 0.0
        doll.meters["clean"] += 1
        out.append("A careful repair made the doll neat again.")
    return out


def _rule_reconcile(world: World) -> list[str]:
    out = []
    child = next(e for e in world.entities.values() if e.kind == "child")
    sibling = next(e for e in world.entities.values() if e.kind == "sibling")
    if child.memes.get("hurt", 0.0) >= THRESHOLD and sibling.memes.get("sorry", 0.0) >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["hurt"] = 0.0
        child.memes["love"] += 1
        sibling.memes["love"] += 1
        child.memes["reconcile"] += 1
        sibling.memes["reconcile"] += 1
        out.append("They both felt better after they said sorry and shared the doll.")
    return out


RULES = [_rule_smudge, _rule_repair, _rule_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            xs = rule(world)
            if xs:
                changed = True
                produced.extend(xs)
    if narrate:
        for x in produced:
            world.say(x)
    return produced


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def predict_outcome(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim.get("child").meters["messy"] += 1
    propagate(sim, narrate=False)
    return {
        "doll_torn": sim.get("doll").meters["torn"] >= THRESHOLD,
        "clean": sim.get("doll").meters["clean"],
    }


def tell(params: StoryParams) -> World:
    world = World(params.setting)
    child = world.add(Entity(id="child", kind="child", type=params.child_type, label=params.child_name))
    sibling = world.add(Entity(id="sibling", kind="sibling", type="boy", label=params.sibling_name))
    parent = world.add(Entity(id="parent", kind="parent", type="adult", label=params.parent_name))
    doll = world.add(Entity(
        id="doll",
        kind="thing",
        type="doll",
        label="doll",
        phrase="a beloved doll",
        owner=child.id,
        caretaker=parent.id,
    ))
    doll.meters["clean"] = 1.0
    if params.doll_state == "torn":
        doll.meters["torn"] = 1.0
        doll.meters["clean"] = 0.0
    elif params.doll_state == "dull":
        doll.meters["clean"] = 0.5

    # Act 1
    world.say(f"In {world.setting}, {child.label} loved {doll.phrase}.")
    if params.doll_state == "plain":
        world.say(f"But the doll looked a little plain, and {child.label} wanted a sweet transformation.")
    elif params.doll_state == "torn":
        world.say(f"The doll had a tiny tear, and {child.label} wanted to make it whole again.")
    else:
        world.say(f"The doll was a little dull, and {child.label} wanted to make it shine.")

    # Act 2
    world.para()
    choice = params.decor
    world.say(f"{child.label} chose to {_safe_lookup(TRANSFORMATIONS, choice)}.")
    child.meters["messy"] += 1
    child.memes["joy"] += 1
    child.memes["pride"] += 1

    prophecy = predict_outcome(world, child)
    if prophecy["doll_torn"]:
        world.say(f"{params.sibling_name} frowned and said the doll should not be changed without asking.")
        sibling.memes["hurt"] += 1
        child.memes["hurt"] += 1
        parent.memes["guide"] = parent.memes.get("guide", 0.0) + 1
        world.say(f"{params.parent_name} gently asked them to pause and talk kindly.")
    else:
        world.say(f"The idea was safe, but it still needed both children to agree.")

    # A small conflict / reconciliation turn
    sibling.memes["sorry"] = 1.0
    world.say(f"Then {params.sibling_name} noticed the worried face and helped fix the little problem.")
    if params.doll_state == "torn":
        world.say(f"They used soft thread and careful hands, which turned the tear into a neat seam.")
    else:
        world.say(f"They added tiny touches until the doll looked happier and brighter.")

    propagate(world, narrate=True)

    # Act 3
    world.para()
    child.memes["love"] += 1
    sibling.memes["love"] += 1
    child.memes["reconcile"] += 1
    sibling.memes["reconcile"] += 1
    doll.meters["clean"] += 0.5

    if child.memes["hurt"] >= THRESHOLD:
        world.say(f"{child.label} and {params.sibling_name} sat close together and said sorry.")
    world.say(
        f"At the end, they admired the doll together: {doll.label} was transformed, repaired, and ready for play."
    )
    world.say(
        f"{child.label} smiled, {params.sibling_name} smiled back, and the little doll looked like it had found a new home in their shared laughter."
    )

    world.facts = {
        "child": child,
        "sibling": sibling,
        "parent": parent,
        "doll": doll,
        "params": params,
        "setting": params.setting,
        "decor": params.decor,
        "transform": _safe_lookup(TRANSFORMATIONS, params.decor),
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming short story about a doll in {f["setting"]} that is transformed and then reconciled after a small disagreement.',
        f"Tell a gentle story where {f['child'].label} and {f['sibling'].label} work together to improve a doll and end with everyone happy.",
        f'Write a simple story that includes a doll, a careful fix, and a kind apology.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sibling = _safe_fact(world, f, "sibling")
    doll = _safe_fact(world, f, "doll")
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"What did {child.label} want to do with the doll in {f['setting']}?",
            answer=f"{child.label} wanted to transform the doll so it would look special and loved again.",
        ),
        QAItem(
            question=f"Why did {sibling.label} feel upset at first?",
            answer=f"{sibling.label} felt upset because the doll changed before they had talked it over together.",
        ),
        QAItem(
            question=f"How did the story end for the doll?",
            answer=f"The doll ended up transformed, carefully repaired, and shared happily between both children.",
        ),
        QAItem(
            question=f"What did the children do to make things better?",
            answer=f"They apologized, listened to each other, and helped fix and decorate the doll together.",
        ),
        QAItem(
            question=f"What was the main change in the doll?",
            answer=f"The doll went from {params.doll_state} to looking bright, cared for, and ready for play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a doll?",
            answer="A doll is a toy made for play and pretend stories. Children often dress it, hold it, and care for it like a tiny friend.",
        ),
        QAItem(
            question="Why can sharing a toy help two children get along?",
            answer="Sharing a toy can help because it gives both children a chance to play, listen, and feel included.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace again after a disagreement, usually by talking kindly and understanding each other.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets fixed, feelings are soothed, and the final picture feels safe and warm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:7} ({e.kind:7}) {e.type:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(self for self in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling and parameter resolution
# ---------------------------------------------------------------------------


def valid_combos() -> list[tuple[str, str]]:
    return [(s, d) for s in SETTINGS for d in DECOR_KINDS]


def explain_rejection(setting: str, decor: str) -> str:
    return f"(No story: the chosen setting '{setting}' and decor '{decor}' do not make a coherent heartwarming transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming doll transformation story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--sibling-name")
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
    ap.add_argument("--doll-state", choices=list(DOLL_STATES))
    ap.add_argument("--decor", choices=list(DECOR_KINDS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "decor", None) and (getattr(args, "setting", None) not in SETTINGS or getattr(args, "decor", None) not in DECOR_KINDS):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    decor = getattr(args, "decor", None) or rng.choice(list(DECOR_KINDS))
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    sibling_name = getattr(args, "sibling_name", None) or rng.choice(SIBLING_NAMES)
    parent_name = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    doll_state = getattr(args, "doll_state", None) or rng.choice(list(DOLL_STATES))
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type=getattr(args, "child_type", None),
        sibling_name=sibling_name,
        parent_name=parent_name,
        doll_state=doll_state,
        decor=decor,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_wrapper())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:")
        for s, d in combos:
            print(f"  {s:8} {d}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            for decor in DECOR_KINDS:
                params = StoryParams(
                    setting=setting,
                    child_name=_safe_lookup(CHILD_NAMES, 0),
                    child_type="girl",
                    sibling_name=_safe_lookup(SIBLING_NAMES, 0),
                    parent_name=_safe_lookup(PARENT_NAMES, 0),
                    doll_state="plain",
                    decor=decor,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            try:
                sample = generate(params)
            except StoryError:
                continue
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
