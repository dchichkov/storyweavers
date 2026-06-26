#!/usr/bin/env python3
"""
storyworlds/worlds/subsidiary_cable_trike_sharing_space_adventure.py
====================================================================

A small space-adventure story world about a child at a moon outpost learning
to share a trike, a tether cable, and a little patch of brave space.

Seed tale sketch:
---
At a tiny subsidiary moon base, a child loves a silver trike that can zip
across the dome floor. One day a second child wants a turn too, but the trike
must stay attached to a safety cable near the airlock. The two children squabble
until the guide robot suggests sharing: one rides while the other helps steer
the cable, then they switch places. In the end they laugh under the stars and
the trike rolls safely home.

This script models that premise as a live world:
- a setting with physical space and a safety cable,
- a prized trike that can be ridden or shared,
- a small tension over turns,
- a compromise that proves the children can share without danger.

The story is authored from simulated state, not a frozen paragraph.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    shared_with: Optional[str] = None
    tethered_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the subsidiary moon base"
    detail: str = "The dome glowed softly, and stars glittered beyond the clear wall."
    allows_share: bool = True


@dataclass
class Ride:
    id: str
    label: str
    phrase: str
    requires_cable: bool = True
    can_share: bool = True
    speed: str = "zoomed"
    keyword: str = "trike"


@dataclass
class Cable:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=lambda: {"tether"})
    shared_use: str = "hold the cable together"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _pron_name(name: str) -> str:
    return name


def _first(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _article(label: str) -> str:
    return f"{_first(label)} {label}"


def _title(label: str) -> str:
    return label[0].upper() + label[1:]


def _ride_turn(world: World) -> list[str]:
    out = []
    rider = world.facts.get("rider")
    friend = world.facts.get("friend")
    ride = world.facts.get("ride")
    cable = world.facts.get("cable")
    if not rider or not friend or not ride:
        return out
    if world.get(ride.id).ridden_by == rider.id and world.get(ride.id).shared_with == friend.id:
        sig = ("turn", ride.id)
        if sig not in world.fired:
            world.fired.add(sig)
            rider.memes["joy"] = rider.memes.get("joy", 0) + 1
            friend.memes["joy"] = friend.memes.get("joy", 0) + 1
            out.append(f"The two of them shared the {ride.label} without a single bump.")
    if cable and world.get(ride.id).tethered_to == cable.id:
        sig = ("safe", ride.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"The {cable.label} kept the {ride.label} safe near the airlock.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    sentences: list[str] = []
    for rule in (_ride_turn,):
        sentences.extend(rule(world))
    if narrate:
        for s in sentences:
            world.say(s)
    return sentences


def tell(setting: Setting, ride_cfg: Ride, cable_cfg: Cable, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, guide_name: str = "Orbit", guide_type: str = "robot") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"joy": 0}, memes={"share": 0}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, meters={"joy": 0}, memes={"share": 0}))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, label="the guide robot"))
    ride = world.add(Entity(id=ride_cfg.id, type="vehicle", label=ride_cfg.label, phrase=ride_cfg.phrase, owner=hero.id, caretaker=guide.id))
    cable = world.add(Entity(id=cable_cfg.id, type="gear", label=cable_cfg.label, phrase=cable_cfg.phrase, caretaker=guide.id))
    ride.tethered_to = cable.id

    world.say(f"{hero.id} lived at {setting.place} and loved the shiny {ride.label}.")
    world.say(f"{setting.detail}")
    world.say(f"Every time {hero.id} saw the {ride.label}, {hero.pronoun().capitalize()} wanted to {_title(ride_cfg.speed)} across the dome floor.")
    world.say(f"But the {ride.label} had to stay tied to the {cable.label} near the airlock.")

    world.para()
    world.say(f"One bright orbit-day, {friend.id} asked for a turn too.")
    world.say(f"{hero.id} hugged the {ride.label} close and frowned.")
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    friend.memes["want"] = friend.memes.get("want", 0) + 1
    if hero.id != friend.id:
        hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
        world.say(f"'{hero.id}, I want to ride too,' said {friend.id}.")
        world.say(f"'{No = None}'" if False else f"'{_title(hero.id)} wants the first turn,' said {hero.id}.")

    world.say(f"The guide robot rolled over and pointed at the cable.")
    world.say(f"'You can share,' it said. 'One child rides, and the other can {_title(cable_cfg.shared_use)}.'")
    hero.memes["mood"] = hero.memes.get("mood", 0) + 0.5
    friend.memes["mood"] = friend.memes.get("mood", 0) + 0.5

    world.para()
    world.say(f"{hero.id} thought about it for a moment, then nodded.")
    world.say(f"{friend.id} held the cable while {hero.id} rode the {ride.label} in a slow circle.")
    ride.ridden_by = hero.id
    ride.shared_with = friend.id
    propagate(world)
    world.say(f"When the circle ended, they switched places.")
    ride.ridden_by = friend.id
    ride.shared_with = hero.id
    propagate(world)
    world.say(f"Now {friend.id} was riding and {hero.id} was helping with the cable.")
    world.say(f"That made the {ride.label} feel like a team instead of a toy.")

    world.para()
    world.say(f"At the end, both children laughed under the moonlight.")
    world.say(f"The {ride.label} rolled back to its charging spot, still safely tied to the {cable.label}.")
    world.say(f"{hero.id} smiled because sharing had made the day feel bigger, not smaller.")
    world.say(f"And at the tiny subsidiary moon base, the stars blinked like they were clapping too.")

    world.facts.update(
        hero=hero,
        friend=friend,
        guide=guide,
        ride=ride,
        cable=cable,
        setting=setting,
    )
    return world


SETTINGS = {
    "moon_base": Setting(
        place="the subsidiary moon base",
        detail="The dome glowed softly, and stars glittered beyond the clear wall.",
    ),
    "dock": Setting(
        place="the little space dock",
        detail="The dock hummed gently, and a row of ships slept beside the bay.",
    ),
    "orbital_garden": Setting(
        place="the orbital garden",
        detail="Tiny leaves drifted in the low gravity, and the path curved like a silver ribbon.",
    ),
}

RIDES = {
    "trike": Ride(
        id="trike",
        label="trike",
        phrase="a bright moon trike with three silver wheels",
        keyword="trike",
        speed="zoom",
    ),
    "spark_trike": Ride(
        id="spark_trike",
        label="spark trike",
        phrase="a spark trike painted with little stars",
        keyword="trike",
        speed="whirl",
    ),
}

CABLES = {
    "safety_cable": Cable(
        id="safety_cable",
        label="safety cable",
        phrase="a long safety cable with a red clip",
    ),
    "blue_cable": Cable(
        id="blue_cable",
        label="blue cable",
        phrase="a blue cable that shimmered like a comet tail",
    ),
}

HERO_NAMES = ["Mina", "Jax", "Lio", "Nori", "Pia", "Tavi"]
FRIEND_NAMES = ["Sol", "Rae", "Bo", "Iris", "Pip", "Kai"]
PEOPLE = {"girl", "boy"}


@dataclass
class StoryParams:
    place: str
    ride: str
    cable: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, r, c) for p in SETTINGS for r in RIDES for c in CABLES]


def explain_rejection(place: str, ride: str, cable: str) -> str:
    return f"(No story: the {ride} and {cable} cannot be shared safely at {place} in this small space adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about sharing a trike and cable.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--cable", choices=CABLES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    place = args.place or rng.choice(sorted(SETTINGS))
    ride = args.ride or rng.choice(sorted(RIDES))
    cable = args.cable or rng.choice(sorted(CABLES))
    if (place, ride, cable) not in combos:
        raise StoryError(explain_rejection(place, ride, cable))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(place=place, ride=ride, cable=cable, hero_name=hero_name, hero_type=hero_type,
                        friend_name=friend_name, friend_type=friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a small child about sharing a {f["ride"].label} and a {f["cable"].label}.',
        f"Tell a gentle story set at {f['setting'].place} where {f['hero'].id} and {f['friend'].id} learn to share the {f['ride'].label}.",
        f'Write a child-friendly story that includes the words "subsidiary", "cable", and "trike".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, ride, cable, setting = f["hero"], f["friend"], f["ride"], f["cable"], f["setting"]
    return [
        QAItem(
            question=f"Who wanted the first turn on the {ride.label}?",
            answer=f"{hero.id} wanted it first, but {friend.id} wanted a turn too at {setting.place}.",
        ),
        QAItem(
            question=f"What helped the children share the {ride.label} safely?",
            answer=f"The {cable.label} helped them share safely because it kept the {ride.label} tied near the airlock.",
        ),
        QAItem(
            question=f"How did the story end at {setting.place}?",
            answer=f"They took turns, laughed under the moonlight, and the {ride.label} rolled back safely while still tied to the {cable.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trike?",
            answer="A trike is a three-wheeled ride that can be easier to balance than a bicycle.",
        ),
        QAItem(
            question="What is a cable?",
            answer="A cable is a strong cord or wire that can hold, connect, or tether things together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something too, often by taking turns or using it together.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.ridden_by:
            bits.append(f"ridden_by={e.ridden_by}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        if e.tethered_to:
            bits.append(f"tethered_to={e.tethered_to}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_place(P) :- place(P).
chosen_ride(R) :- ride(R).
chosen_cable(C) :- cable(C).
valid(P,R,C) :- chosen_place(P), chosen_ride(R), chosen_cable(C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in RIDES:
        lines.append(asp.fact("ride", r))
    for c in CABLES:
        lines.append(asp.fact("cable", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        RIDES[params.ride],
        CABLES[params.cable],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
    )
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
    StoryParams(place="moon_base", ride="trike", cable="safety_cable", hero_name="Mina", hero_type="girl",
                friend_name="Sol", friend_type="boy"),
    StoryParams(place="dock", ride="spark_trike", cable="blue_cable", hero_name="Jax", hero_type="boy",
                friend_name="Rae", friend_type="girl"),
    StoryParams(place="orbital_garden", ride="trike", cable="blue_cable", hero_name="Pia", hero_type="girl",
                friend_name="Kai", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid space-adventure combos:\n")
        for p, r, c in combos:
            print(f"  {p:14} {r:12} {c}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
