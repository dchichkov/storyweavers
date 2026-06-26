#!/usr/bin/env python3
"""
A standalone storyworld about a child, a totem, and a warm teamwork fix for
something that has started to ravel.

Premise:
- A child loves a handmade totem used for a little celebration or family rite.
- The totem has soft ribbons and string that can ravel when the child takes it
  outside or carries it too quickly.
- A caregiver notices the tangle, warns gently, and the child feels disappointed.
- Instead of forbidding the fun, they work together: one holds, one smooths,
  one ties, and the totem is made lovely again.

This world is built to read like a heartwarming TinyStories-style tale, but it
still uses a real simulation: objects have physical meters, people have emotional
memes, and the ending changes because the state changes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Small threshold for state changes to become narratively relevant.
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["ravel", "smooth", "steady", "bright", "clean"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "worry", "patience", "pride", "conflict", "helpfulness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _ravel(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["ravel"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id:
                continue
            if item.kind != "thing":
                continue
            if item.label != "totem":
                continue
            sig = ("ravel", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["ravel"] += 1
            item.meters["clean"] = max(0.0, item.meters["clean"] - 1)
            out.append(f"{item.label.capitalize()} strings started to ravel in the breeze.")
    return out


def _tangle_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.label != "totem":
            continue
        if item.meters["ravel"] < THRESHOLD:
            continue
        caretaker = world.get(item.caretaker) if item.caretaker else None
        if not caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker.memes["worry"] += 1
        out.append(f"That made {caretaker.label} worry a little.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_ravel, _tangle_worry):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the community hall", indoors=True, affords={"totem_dance", "totem_parade"})

ACTIVITY = Activity(
    id="totem_parade",
    verb="carry the totem in the parade",
    gerund="carrying the totem in the parade",
    rush="hurry down the hall",
    mess="ravel",
    soil="all raveled",
    zone={"hands", "torso"},
    keyword="totem",
    tags={"totem", "teamwork", "ravel"},
)

PRIZE = Prize(
    label="totem",
    phrase="a bright handmade totem with ribbon tails",
    type="totem",
    region="hands",
)

FIX = Fix(
    id="untangle",
    label="a calm untangling plan",
    prep="hold the totem still and smooth the ribbons together",
    tail="worked side by side until the ribbons lay flat again",
    covers={"hands", "torso"},
    guards={"ravel"},
)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    friend: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Maya", "Nia", "Lila", "Zoe", "Ava", "Mina"]
BOY_NAMES = ["Noah", "Finn", "Leo", "Owen", "Theo", "Eli"]
FRIENDS = ["Jules", "Pip", "Rory", "Milo", "Tess", "Bea"]
TRAITS = ["careful", "cheerful", "patient", "gentle", "curious", "brave"]


def tell(name: str, gender: str, parent: str, friend: str, trait: str) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait, "kind"]))
    caregiver = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    helper = world.add(Entity(id=friend, kind="character", type="child", label=friend))
    totem = world.add(Entity(
        id="totem",
        kind="thing",
        type="totem",
        label="totem",
        phrase="a bright handmade totem with ribbon tails",
        owner=child.id,
        caretaker=caregiver.id,
    ))

    child.memes["love"] += 1
    child.memes["pride"] += 1
    caregiver.memes["love"] += 1
    helper.memes["joy"] += 1

    world.say(f"{child.id} was a little {trait} {gender} who loved {totem.phrase}.")
    world.say(f"{child.id}'s {parent} helped make it, and {child.id} carried it like a treasure.")

    world.para()
    world.say(f"One afternoon at {world.setting.place}, {child.id} wanted to {ACTIVITY.verb}.")
    world.say(f"The hall was full of happy feet and soft music, and everyone was ready for the parade.")
    child.meters["ravel"] += 1
    world.zone = set(ACTIVITY.zone)
    propagate(world, narrate=True)

    world.say(f"{caregiver.label.capitalize()} noticed the ribbon tails snagging and said, "
              f"\"If we keep going like this, the {totem.label} will get {ACTIVITY.soil}.\"")
    caregiver.memes["worry"] += 1
    child.memes["conflict"] += 1
    child.memes["sadness"] = 1.0
    world.say(f"{child.id} felt a small pinch in {child.pronoun('possessive')} chest and wanted to fix it fast.")

    world.para()
    helper.memes["helpfulness"] += 1
    caregiver.memes["patience"] += 1
    world.say(f"Then {friend} stepped closer and said, \"We can help.\"")
    world.say(f"{child.id}, {friend}, and {caregiver.label} made {FIX.label}: {FIX.prep}.")
    totem.meters["ravel"] = 0.0
    totem.meters["clean"] += 1
    child.memes["conflict"] = 0.0
    child.memes["joy"] += 1
    child.memes["love"] += 1
    caregiver.memes["worry"] = 0.0
    caregiver.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(f"They {FIX.tail}.")

    world.para()
    world.say(
        f"At last, {child.id} lifted the {totem.label} high, the ribbons stayed smooth, "
        f"and the little parade went on with three proud smiles and one very lovely {totem.label}."
    )

    world.facts = {
        "child": child,
        "caregiver": caregiver,
        "helper": helper,
        "totem": totem,
        "activity": ACTIVITY,
        "fix": FIX,
        "setting": SETTING,
    }
    return world


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "hall"), asp.fact("indoors", "hall")]
    lines.append(asp.fact("affords", "hall", ACTIVITY.id))
    lines.append(asp.fact("activity", ACTIVITY.id))
    lines.append(asp.fact("mess_of", ACTIVITY.id, ACTIVITY.mess))
    for r in sorted(ACTIVITY.zone):
        lines.append(asp.fact("splashes", ACTIVITY.id, r))
    lines.append(asp.fact("prize", "totem"))
    lines.append(asp.fact("worn_on", "totem", PRIZE.region))
    lines.append(asp.fact("gear", FIX.id))
    for g in sorted(FIX.guards):
        lines.append(asp.fact("guards", FIX.id, g))
    for c in sorted(FIX.covers):
        lines.append(asp.fact("covers", FIX.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid_story(hall, A, P) :- affords(hall, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about a totem and teamwork.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--friend")
    ap.add_argument("--trait")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    friend = args.friend or rng.choice(FRIENDS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, friend=friend, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a heartwarming story for a little child about a totem that starts to ravel and a family that fixes it together.',
        f"Tell a gentle story where {child.id} carries a totem at {f['setting'].place} and learns teamwork when the ribbon tails tangle.",
        f'Write a short story that includes the word "totem" and ends with everyone smiling after untangling it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    helper = f["helper"]
    totem = f["totem"]
    return [
        QAItem(
            question=f"What did {child.id} love to carry?",
            answer=f"{child.id} loved carrying the {totem.label}, a bright handmade treasure with ribbon tails.",
        ),
        QAItem(
            question=f"Who helped when the {totem.label} started to ravel?",
            answer=f"{caregiver.label.capitalize()} and {helper.id} helped {child.id} fix the {totem.label} together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the ribbons lying flat again and {child.id} smiling because the {totem.label} was ready for the parade.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What does it mean when something ravels?",
            answer="When something ravels, its threads or strings start to come loose and twist into a tangle.",
        ),
        QAItem(
            question="Why can a ribbon get tangled?",
            answer="A ribbon can get tangled when it moves a lot, brushes other things, or gets pulled without care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.friend, params.trait)
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


CURATED = [
    StoryParams(name="Maya", gender="girl", parent="mother", friend="Pip", trait="gentle"),
    StoryParams(name="Noah", gender="boy", parent="father", friend="Tess", trait="careful"),
    StoryParams(name="Lila", gender="girl", parent="mother", friend="Jules", trait="cheerful"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("hall", ACTIVITY.id, "totem")}
    if asp_set == py_set:
        print("OK: ASP and Python reasonability gates agree.")
        return 0
    print("MISMATCH:", asp_set, py_set)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(vals)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} ({p.gender})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
