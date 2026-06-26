#!/usr/bin/env python3
"""
A nursery-rhyme style story world about a child, a scooter, and a gentle lesson
learned through bravery and transformation.

Premise:
- A small child loves scooting fast.
- The child wants to keep riding, but a sore hip and a wobbly scooter make the
  day risky.
- A caring grownup helps the child choose a safer way, and the child grows
  braver, learns a lesson, and changes how they ride.

This world keeps the story grounded in a tiny simulation:
- body-state meters track hip soreness, steadiness, and energy
- emotion memes track fear, bravery, relief, and pride
- narration is driven by state transitions, not a frozen template
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lane"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Ride:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the lane", affords={"scooter"}),
    "yard": Setting(place="the yard", affords={"scooter"}),
    "path": Setting(place="the garden path", affords={"scooter"}),
}

RIDES = {
    "scooter": Ride(
        id="scooter",
        verb="ride the scooter",
        gerund="riding the scooter",
        rush="zip down the lane",
        risk="wobble and tip",
        zone={"legs", "hip"},
        keyword="scooter",
        tags={"scooter", "wheels"},
    ),
}

AIDS = {
    "helmet": Aid(
        id="helmet",
        label="a snug helmet",
        covers={"head"},
        helps={"fear"},
        prep="put on a snug helmet",
        tail="rolled on with a safer spark",
    ),
    "pad": Aid(
        id="hip_pad",
        label="a soft hip pad",
        covers={"hip"},
        helps={"hip"},
        prep="strap on a soft hip pad",
        tail="glided on with a gentler bounce",
    ),
}

NAMES = ["Mia", "Pip", "Nell", "Toby", "Luna", "Finn"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["spry", "curious", "bold", "cheery", "tiny"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
ride_risk(R) :- ride(R), zone(R, hip).
safe_fix(R, A) :- ride_risk(R), aid(A), covers(A, hip).
good_story(S, R) :- setting(S), affords(S, R), safe_fix(R, _).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for rid, r in RIDES.items():
        lines.append(asp.fact("ride", rid))
        for z in sorted(r.zone):
            lines.append(asp.fact("zone", rid, z))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for c in sorted(a.covers):
            lines.append(asp.fact("covers", aid, c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {(place, ride_id) for place, s in SETTINGS.items() for ride_id in s.affords if ride_id == "scooter"}
    if asp_set == py_set:
        print(f"OK: ASP matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def can_fix(ride: Ride, aid: Aid) -> bool:
    return ride.id == "scooter" and "hip" in ride.zone and "hip" in aid.covers

def valid_story(place: str, ride_id: str, aid_id: str) -> bool:
    return place in SETTINGS and ride_id in RIDES and aid_id in AIDS and can_fix(RIDES[ride_id], AIDS[aid_id])

def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.ride and args.ride not in RIDES:
        raise StoryError("Unknown ride.")
    if args.aid and args.aid not in AIDS:
        raise StoryError("Unknown aid.")

    candidates = [
        (place, ride_id, aid_id)
        for place, setting in SETTINGS.items()
        for ride_id in setting.affords
        for aid_id in AIDS
        if valid_story(place, ride_id, aid_id)
        and (args.place is None or place == args.place)
        and (args.ride is None or ride_id == args.ride)
        and (args.aid is None or aid_id == args.aid)
    ]
    if not candidates:
        raise StoryError("No valid combination matches the given options.")

    place, ride_id, aid_id = rng.choice(candidates)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        ride=ride_id,
        aid=aid_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


@dataclass
class StoryParams:
    place: str
    ride: str
    aid: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    ride = world.add(Entity(id="Ride", type="scooter", label="scooter", caretaker=hero.id))
    aid = world.add(Entity(id=params.aid, type="aid", label=AIDS[params.aid].label, owner=hero.id))

    hero.meters["energy"] = 2.0
    hero.meters["hip"] = 0.0
    hero.memes["bravery"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["pride"] = 0.0
    parent.memes["care"] = 1.0
    ride.meters["wobble"] = 1.0

    world.facts.update(hero=hero, parent=parent, ride=ride, aid=aid, ride_cfg=RIDES[params.ride], setting=world.setting)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    ride_cfg: Ride = f["ride_cfg"]
    aid: Entity = f["aid"]
    setting: Setting = f["setting"]

    world.say(f"{hero.id} was a {f['hero'].pronoun('subject').capitalize()}?")  # replaced below
    world.paragraphs = [[]]  # reset the accidental line cleanly

    world.say(f"{hero.id} was a little {hero.type} with a bright grin.")
    world.say(f"{hero.id} loved {ride_cfg.gerund} near {setting.place}.")
    world.say(f"{hero.id}'s {world.get('Ride').label} was quick, but it could {ride_cfg.risk}.")

    world.para()
    hero.memes["fear"] += 1.0
    hero.meters["hip"] += 1.0
    world.say(f"One day, {hero.id} felt a twinge in the hip, and the scooter seemed to sway.")
    world.say(f"{hero.id} still wanted to {ride_cfg.verb}, but {hero.pronoun('possessive')} {parent.label} watched the wobble with worry.")

    # The parent predicts trouble and offers a fix.
    if hero.meters["hip"] >= THRESHOLD:
        world.say(f'"If you rush," said {parent.id}, "your hip may hurt more, and the scooter may tip."')
    world.say(f"Then came a tiny pause, as quiet as a cloud.")

    world.para()
    hero.memes["bravery"] += 1.0
    world.say(f"{hero.id} took a breath and chose the brave thing: to listen and learn.")
    if aid.id == "hip_pad":
        world.say(f"{parent.id} helped {hero.id} {AIDS[aid.id].prep}, and the sore hip felt snug and held.")
    else:
        world.say(f"{parent.id} helped {hero.id} {AIDS[aid.id].prep}, and the morning felt steadier already.")
    world.say(f"That was the lesson learned: slow can be safe, and safe can still be fun.")

    hero.memes["fear"] = 0.0
    hero.memes["pride"] += 1.0
    hero.memes["bravery"] += 1.0
    hero.meters["hip"] = 0.0
    ride.meters["wobble"] = 0.0

    world.para()
    world.say(f"So {hero.id} rode again, but gentler now, {ride_cfg.gerund} with a softer grin.")
    world.say(f"The scooter sang down the lane, and {hero.id} felt a transformation from shaky to sure.")
    world.say(f"By the end, {hero.id} was bright with bravery, and even the little hip had settled to rest.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    ride_cfg: Ride = f["ride_cfg"]
    setting: Setting = f["setting"]
    return [
        f'Write a nursery-rhyme style story about {hero.id}, a scooter, and a gentle lesson learned at {setting.place}.',
        f'Tell a child-facing tale where a small rider wants to {ride_cfg.verb} but learns bravery and transformation.',
        f'Write a short, rhythmic story that includes the words "hip", "scooter", and "slimming" in a meaningful way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    ride_cfg: Ride = f["ride_cfg"]
    aid: Entity = f["aid"]

    return [
        QAItem(
            question=f"What did {hero.id} love to do at first?",
            answer=f"{hero.id} loved to {ride_cfg.verb} near {world.setting.place}."
        ),
        QAItem(
            question=f"What was hurting {hero.id} in the story?",
            answer=f"{hero.id}'s hip was sore, so riding fast did not feel wise."
        ),
        QAItem(
            question=f"Who helped {hero.id} make the scooter plan safer?",
            answer=f"{parent.id} helped {hero.id} choose a safer way and use {aid.label}."
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The lesson learned was that going more slowly can keep you safe and still let you have fun."
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} changed from wobbly and worried to brave and steady."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scooter?",
            answer="A scooter is a small ride with wheels and a handlebar that a child can push along."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the careful or hard thing even when you feel nervous."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one way of being to another."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about hip, scooter, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for ride_id in setting.affords:
            for aid_id in AIDS:
                if valid_story(place, ride_id, aid_id):
                    out.append((place, ride_id, aid_id))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for i, (place, ride_id, aid_id) in enumerate(valid_combos()):
            params = StoryParams(
                place=place,
                ride=ride_id,
                aid=aid_id,
                name=NAMES[i % len(NAMES)],
                gender=GENDERS[i % len(GENDERS)],
                parent=PARENTS[i % len(PARENTS)],
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
