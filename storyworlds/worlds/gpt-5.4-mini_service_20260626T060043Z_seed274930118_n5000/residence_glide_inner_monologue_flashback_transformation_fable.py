#!/usr/bin/env python3
"""
storyworlds/worlds/residence_glide_inner_monologue_flashback_transformation_fable.py
===================================================================================

A small fable-style storyworld about a resident who longs to glide, remembers
an earlier lesson, and changes in a meaningful way.

The world model tracks a character in a residence, a fragile path, a possible
gliding motion, inner monologue, a flashback to a past mistake, and a
transformation from impatience to care.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "queen", "lady", "owl"}
        male = {"boy", "father", "man", "brother", "king", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label


@dataclass
class Residence:
    place: str = "the old house"
    kind: str = "house"
    gloss: str = "a polished wooden hallway"
    affords: set[str] = field(default_factory=set)
    fragile: bool = False


@dataclass
class Path:
    label: str
    phrase: str
    risk: str
    safe_method: str
    motion: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, residence: Residence) -> None:
        self.residence = residence
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy

        w = World(self.residence)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not hero:
        return out
    path: Path = world.facts["path"]
    if hero.meters.get("glide", 0.0) < THRESHOLD:
        return out
    if hero.meters.get("steady", 0.0) >= THRESHOLD:
        return out
    sig = ("slip", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1
    out.append(f"{hero.name_word()} wobbled on the {path.label}.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not hero:
        return out
    if hero.memes.get("memory", 0.0) < THRESHOLD:
        return out
    sig = ("calm", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["patience"] = hero.memes.get("patience", 0.0) + 1
    hero.memes["rush"] = max(0.0, hero.memes.get("rush", 0.0) - 1)
    out.append(f"The remembered lesson made {hero.name_word()} slow down.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not hero:
        return out
    if hero.memes.get("patience", 0.0) < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 1)
    out.append(f"{hero.name_word()} felt different inside, as if a small door had opened.")
    return out


CAUSAL_RULES = [_r_slip, _r_calm, _r_transform]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    residence: str
    path: str
    name: str
    kind: str
    seed: Optional[int] = None


RESIDENCES = {
    "house": Residence(place="the old house", kind="house", gloss="a polished wooden hallway", affords={"glide"}),
    "tower": Residence(place="the round tower", kind="tower", gloss="a narrow stairwell", affords={"glide"}),
    "barn": Residence(place="the quiet barn loft", kind="barn", gloss="a smooth loft beam", affords={"glide"}),
}

PATHS = {
    "hall": Path(
        label="hallway",
        phrase="the long hallway",
        risk="the floor was too slick",
        safe_method="walk with careful steps",
        motion="glide along the hallway",
        keyword="glide",
        tags={"glide", "home"},
    ),
    "stair": Path(
        label="stair rail",
        phrase="the stair rail",
        risk="the rail could send someone tumbling",
        safe_method="hold the rail and step slowly",
        motion="glide down the rail",
        keyword="glide",
        tags={"glide", "home"},
    ),
    "beam": Path(
        label="beam",
        phrase="the loft beam",
        risk="the beam was narrow and could toss a careless traveler",
        safe_method="cross only after a pause",
        motion="glide across the beam",
        keyword="glide",
        tags={"glide", "home"},
    ),
}

NAMES = {
    "fox": ["Pip", "Milo", "Tarin", "Wren", "Rowan"],
    "owl": ["Nia", "Mara", "Luna", "Sera", "Dove"],
    "badger": ["Bram", "Hugo", "Toby", "Nestor", "Puck"],
}

KINDS = {
    "fox": "fox",
    "owl": "owl",
    "badger": "badger",
}


def valid_combos() -> list[tuple[str, str]]:
    return [(r, p) for r in RESIDENCES for p in PATHS if "glide" in RESIDENCES[r].affords]


def explain_rejection(residence: Residence, path: Path) -> str:
    return (
        f"(No story: {residence.place} does not reasonably support {path.motion}; "
        f"try a residence with a smooth inside path.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-style story world: residence, glide, inner monologue, flashback, transformation."
    )
    ap.add_argument("--residence", choices=RESIDENCES)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    combos = valid_combos()
    if args.residence and args.path:
        if (args.residence, args.path) not in combos:
            raise StoryError(explain_rejection(RESIDENCES[args.residence], PATHS[args.path]))
    choices = [c for c in combos if (not args.residence or c[0] == args.residence) and (not args.path or c[1] == args.path)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    residence, path = rng.choice(sorted(choices))
    kind = args.kind or rng.choice(sorted(KINDS))
    name = args.name or rng.choice(NAMES[kind])
    return StoryParams(residence=residence, path=path, name=name, kind=kind)


def tell(params: StoryParams) -> World:
    world = World(RESIDENCES[params.residence])
    path = PATHS[params.path]
    hero = world.add(Entity(id=params.name, kind="character", type=params.kind, label=params.name, traits=["young", "restless"]))
    old_self = "the younger version of {}"
    hero.meters["glide"] = 0.0
    hero.meters["steady"] = 0.0
    hero.memes["rush"] = 1.0
    hero.memes["pride"] = 1.0
    hero.memes["memory"] = 0.0
    hero.memes["kindness"] = 0.0
    world.facts.update(hero=hero, path=path, residence=world.residence)

    world.say(f"{hero.name_word()} lived in {world.residence.place}, where {world.residence.gloss} always waited.")
    world.say(f"{hero.pronoun().capitalize()} loved to {path.motion}, because the motion felt almost like flying.")
    world.say(f"Still, a little voice inside asked, 'Will I be careful, or will I rush again?'")

    world.para()
    world.say(
        f"One quiet afternoon, {hero.name_word()} stood at {path.phrase} and wanted to go at once."
    )
    hero.meters["glide"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then a flashback visited {hero.name_word()}: once, when {old_self.format(hero.name_word())} tried to hurry, "
        f"{hero.pronoun('object')} had slipped and frightened everyone in the home."
    )
    hero.memes["memory"] += 1
    world.say(
        f"The memory spoke in {hero.pronoun('possessive')} mind: 'Fast feet are not always wise feet.'"
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.name_word()} took a breath and listened to the thought that followed: "
        f"'If I {path.safe_method}, I can still {path.motion} without harm.'"
    )
    hero.meters["steady"] += 1
    hero.memes["patience"] = hero.memes.get("patience", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(
        f"So {hero.name_word()} changed. {hero.pronoun().capitalize()} no longer chased the moment, but moved with care."
    )
    world.say(
        f"At last, {hero.name_word()} did {path.motion}, and the whole residence seemed softer for the choice."
    )
    world.say(
        f"And the lesson stayed behind like a lantern: the one who glides with wisdom goes farther than the one who rushes."
    )

    world.facts["transformed"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    path = f["path"]
    res = f["residence"]
    return [
        f"Write a short fable about a {hero.type} who lives in {res.place} and wants to {path.motion}.",
        f"Tell a child-friendly story with an inner monologue, a flashback, and a transformation, using the word 'glide'.",
        f"Write a gentle moral tale set in {res.place} where {hero.label} learns to choose care over haste.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    path = f["path"]
    res = f["residence"]
    return [
        QAItem(
            question=f"Where did {hero.name_word()} live?",
            answer=f"{hero.name_word()} lived in {res.place}.",
        ),
        QAItem(
            question=f"What did {hero.name_word()} want to do on the {path.label}?",
            answer=f"{hero.name_word()} wanted to {path.motion}.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.name_word()} about?",
            answer=f"The flashback reminded {hero.name_word()} that rushing could cause a slip and frighten everyone.",
        ),
        QAItem(
            question=f"How did {hero.name_word()} change by the end?",
            answer=f"{hero.name_word()} changed from rushing to being careful and patient.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a residence?",
            answer="A residence is a place where someone lives, like a house, tower, or barn loft.",
        ),
        QAItem(
            question="What does it mean to glide?",
            answer="To glide means to move smoothly and lightly, almost as if you are floating.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thoughts spoken inside the story.",
        ),
        QAItem(
            question="What is transformation in a fable?",
            answer="Transformation is a meaningful change in a character, such as becoming wiser or kinder.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(residence="house", path="hall", name="Pip", kind="fox"),
    StoryParams(residence="tower", path="stair", name="Luna", kind="owl"),
    StoryParams(residence="barn", path="beam", name="Bram", kind="badger"),
]


ASP_RULES = r"""
valid(Residence, Path) :- residence(Residence), path(Path), affords(Residence, glide), uses(Path, glide).
show_valid(Residence, Path) :- valid(Residence, Path).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, res in RESIDENCES.items():
        lines.append(asp.fact("residence", rid))
        for a in sorted(res.affords):
            lines.append(asp.fact("affords", rid, a))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("uses", pid, "glide"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world: residence, glide, inner monologue, flashback, transformation.")
    ap.add_argument("--residence", choices=RESIDENCES)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    if args.residence and args.path and (args.residence, args.path) not in valid_combos():
        raise StoryError(explain_rejection(RESIDENCES[args.residence], PATHS[args.path]))
    combos = [c for c in valid_combos() if (not args.residence or c[0] == args.residence) and (not args.path or c[1] == args.path)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    residence, path = rng.choice(sorted(combos))
    kind = args.kind or rng.choice(sorted(KINDS))
    name = args.name or rng.choice(NAMES[kind])
    return StoryParams(residence=residence, path=path, name=name, kind=kind)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
            header = f"### {p.name}: {p.path} in {p.residence}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
