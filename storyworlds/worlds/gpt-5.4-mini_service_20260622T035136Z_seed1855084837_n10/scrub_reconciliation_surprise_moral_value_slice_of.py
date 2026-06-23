#!/usr/bin/env python3
"""
storyworlds/worlds/scrub_reconciliation_surprise_moral_value_slice_of.py
========================================================================

A small slice-of-life story world about a child, a minor mess, an unexpected
surprise, and a reconciliation that lands on a gentle moral value.

Core premise:
- A child makes a small mess while trying to help or decorate.
- A sibling/friend/neighbor is hurt or annoyed.
- A careful scrub and an unexpected surprise open the door to apology.
- The story ends with reconciliation and a concrete changed image.

This script is standalone and uses only the Python stdlib plus the shared
storyworlds/results.py containers. ASP/clingo integration is loaded lazily.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Robust direct-import path setup: walk upward until we find results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_SCAN = _HERE
while True:
    if os.path.exists(os.path.join(_SCAN, "results.py")):
        if _SCAN not in sys.path:
            sys.path.insert(0, _SCAN)
        break
    parent = os.path.dirname(_SCAN)
    if parent == _SCAN:
        break
    _SCAN = parent

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    partner: Optional[str] = None
    location: str = ""
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "clean": 0.0, "hurt": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "hurt": 0.0, "pride": 0.0, "regret": 0.0, "warmth": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    mishap: str
    mess_kind: str
    location: str
    risk: str
    keyword: str = "scrub"
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    location: str
    material: str
    clean_method: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseCfg:
    id: str
    label: str
    reveal: str
    value: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    act: str
    object: str
    surprise: str
    name: str
    kind: str
    partner_name: str
    partner_kind: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", atmosphere="warm and busy", supports={"scrub"}),
    "porch": Setting(id="porch", place="the porch", atmosphere="bright and breezy", supports={"scrub"}),
    "laundry": Setting(id="laundry", place="the laundry room", atmosphere="quiet and tiled", supports={"scrub"}),
}

ACTS = {
    "paint": Act(id="paint", verb="paint a sign", gerund="painting a sign", mishap="painted", mess_kind="paint", location="the table", risk="a bright drip on the floor", keyword="scrub", tags={"paint", "mess"}),
    "mud": Act(id="mud", verb="carry in muddy boots", gerund="carrying in muddy boots", mishap="muddy", mess_kind="mud", location="the mat", risk="mud marks on the rug", keyword="scrub", tags={"mud", "mess"}),
    "juice": Act(id="juice", verb="pour juice for everyone", gerund="pouring juice", mishap="sticky", mess_kind="juice", location="the counter", risk="a sticky spill", keyword="scrub", tags={"juice", "mess"}),
}

OBJECTS = {
    "floor": ObjectCfg(id="floor", label="floor", phrase="the floor", location="the floor", material="tile", clean_method="scrub"),
    "table": ObjectCfg(id="table", label="table", phrase="the table", location="the table", material="wood", clean_method="wipe"),
    "mat": ObjectCfg(id="mat", label="mat", phrase="the mat", location="the mat", material="fabric", clean_method="scrub"),
}

SURPRISES = {
    "cake": SurpriseCfg(id="cake", label="a small cake", reveal="a small cake with two candles", value="kindness", tags={"cake", "value"}),
    "note": SurpriseCfg(id="note", label="a note", reveal="a handwritten note saying 'thank you'", value="gratitude", tags={"note", "value"}),
    "flowers": SurpriseCfg(id="flowers", label="flowers", reveal="a little vase of flowers by the sink", value="care", tags={"flowers", "value"}),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Ada", "Nora", "Maya", "Ivy", "Lia"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Finn", "Eli", "Noah", "Zane", "Leo"]
TRAITS = ["gentle", "curious", "patient", "thoughtful", "cheerful", "careful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTS:
            for o in OBJECTS:
                for su in SURPRISES:
                    combos.append((s, a, o, su))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not support a small scrub-and-reconcile slice of life.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: scrub, surprise, reconciliation, moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-kind", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.act is None or c[1] == args.act)
              and (args.object is None or c[2] == args.object)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, act, obj, surprise = rng.choice(sorted(combos))
    kind = args.kind or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if kind == "girl" else BOY_NAMES)
    partner_kind = args.partner_kind or ("boy" if kind == "girl" else "girl")
    partner_name = args.partner_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, act=act, object=obj, surprise=surprise, name=name, kind=kind, partner_name=partner_name, partner_kind=partner_kind, parent=parent, trait=trait)


def _make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type=params.kind, role="child", traits=[params.trait], partner=params.partner_name))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_kind, role="partner", traits=["steady"], partner=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="Parent"))
    obj = world.add(Entity(id=params.object, kind="thing", type=params.object, label=params.object, phrase=OBJECTS[params.object].phrase, location=OBJECTS[params.object].location))
    surprise = world.add(Entity(id=params.surprise, kind="thing", type="surprise", label=SURPRISES[params.surprise].label, phrase=SURPRISES[params.surprise].reveal, location="nearby", attrs={"value": SURPRISES[params.surprise].value}))
    return world


def _render_story(world: World, params: StoryParams) -> str:
    child = world.get(params.name)
    partner = world.get(params.partner_name)
    parent = world.get("Parent")
    obj = world.get(params.object)
    surprise = world.get(params.surprise)
    act = ACTS[params.act]
    lines = [
        f"{child.id} and {partner.id} had a quiet afternoon in {world.setting.place}.",
        f"{child.id} wanted to {act.verb}, and soon there was {act.risk} on {obj.phrase}.",
    ]
    child.meters["mess"] += 1
    child.memes["regret"] += 1
    partner.memes["hurt"] += 1
    world.facts["mess_kind"] = act.mess_kind
    world.facts["object"] = obj.id
    world.facts["surprise"] = surprise.id
    world.facts["parent"] = parent.id
    lines.append(f"{partner.id} frowned because the room no longer felt neat.")
    lines.append(f"Then {world.facts['parent']} led them to a surprise: {surprise.phrase}.")
    child.memes["warmth"] += 1
    partner.memes["warmth"] += 1
    lines.append(f"{child.id} paused, smiled, and said sorry.")
    obj.meters["clean"] += 1
    child.meters["mess"] = 0.0
    partner.memes["hurt"] = 0.0
    child.memes["pride"] += 1
    lines.append(f"Together they scrubbed {obj.phrase} until it shone again, and the surprise felt even kinder after the apology.")
    lines.append(f"By evening, {child.id} and {partner.id} were side by side again, and the little home felt peaceful.")
    world.facts["reconciled"] = True
    world.facts["moral_value"] = SURPRISES[params.surprise].value
    return " ".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    story = _render_story(world, params)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a slice-of-life story where {p.get('mess_kind', 'a small mess')} is cleaned up with a scrub and ends in reconciliation.",
        f"Tell a gentle story with a surprise that helps two children apologize and make peace.",
        "Write a child-facing story about a messy moment, a calm cleanup, and a moral value like kindness or gratitude.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = next(e for e in world.entities.values() if e.role == "child")
    partner = next(e for e in world.entities.values() if e.role == "partner")
    obj = world.get(f["object"])
    surprise = world.get(f["surprise"])
    return [
        QAItem(question=f"Why did {child.id} and {partner.id} need to scrub {obj.phrase}?", answer=f"They needed to scrub {obj.phrase} because {child.id} made a small mess while trying to help. Scrubbing turned the messy spot back into something neat."),
        QAItem(question=f"What surprise did {world.facts['parent']} show them?", answer=f"{world.facts['parent']} showed them {surprise.phrase}, which changed the mood and made the apology feel welcome. The surprise helped the two children soften toward each other."),
        QAItem(question=f"How did the story end between {child.id} and {partner.id}?", answer=f"They reconciled. After the scrub and the apology, they were peaceful together again and the room felt calm."),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What does scrub mean in this world?", answer="Scrub means to work at a dirty surface with patient cleaning until the mess comes off. In this story it is the step that helps fix the problem."),
        QAItem(question="Why is apology important here?", answer="An apology matters because it helps people feel heard after a small hurt. In the story, saying sorry opens the door to reconciliation."),
        QAItem(question="What moral value is shown at the end?", answer=f"The story shows kindness and gratitude. The surprise and the cleanup both lead the children back to being gentle with each other."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id}: {e.kind} {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,O,Su) :- setting(S), act(A), object(O), surprise(Su).
reconciled :- valid(_,_,_,_).
moral_value(kindness).
moral_value(gratitude).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTS:
        lines.append(asp.fact("act", a))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for su in SURPRISES:
        lines.append(asp.fact("surprise", su))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    ok1 = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(StoryParams(setting="kitchen", act="paint", object="floor", surprise="cake", name="Mina", kind="girl", partner_name="Owen", partner_kind="boy", parent="mother", trait="gentle"))
        ok2 = bool(sample.story)
    except Exception:
        ok2 = False
    if ok1 and ok2:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    if not ok1:
        print("MISMATCH: ASP and Python valid combos differ.")
    if not ok2:
        print("MISMATCH: generation smoke test failed.")
    return 1


def explain_params(args: argparse.Namespace) -> StoryParams:
    return resolve_params(args, random.Random(args.seed if args.seed is not None else random.randrange(2**31)))


CURATED = [
    StoryParams(setting="kitchen", act="paint", object="floor", surprise="cake", name="Mina", kind="girl", partner_name="Owen", partner_kind="boy", parent="mother", trait="gentle"),
    StoryParams(setting="porch", act="mud", object="mat", surprise="note", name="Leo", kind="boy", partner_name="Nora", partner_kind="girl", parent="father", trait="careful"),
    StoryParams(setting="laundry", act="juice", object="table", surprise="flowers", name="Tia", kind="girl", partner_name="Ben", partner_kind="boy", parent="mother", trait="thoughtful"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
