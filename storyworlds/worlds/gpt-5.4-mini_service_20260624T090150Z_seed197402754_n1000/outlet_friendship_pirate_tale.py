#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/outlet_friendship_pirate_tale.py
==============================================================================================================

A small storyworld about a pirate friend pair at the outlet, where water meets
the sea and a little problem can turn into a teamwork tale.
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

TITLE = "Outlet Friendship Pirate Tale"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    ally: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    tide: str
    sparkle: str


@dataclass
class Hazard:
    id: str
    verb: str
    mess: str
    risk: str
    zone: str
    weather: str


@dataclass
class Rescue:
    id: str
    label: str
    phrase: str
    fix: str
    covers: str


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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    ship = world.get(world.facts["ship"].id)
    if hero.meters.get(world.facts["hazard"].id, 0) < 1:
        return out
    sig = ("soak", ship.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.meters["wet"] = ship.meters.get("wet", 0) + 1
    ship.meters["stuck"] = ship.meters.get("stuck", 0) + 1
    out.append(f"The little ship got wet and stuck near the rocks.")
    return out


CAUSAL_RULES = [
    _r_soak,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_world(hero_name: str, friend_name: str, setting: Setting, hazard: Hazard, rescue: Rescue) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name, meters={}, memes={}))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl", label=friend_name, meters={}, memes={}))
    ship = world.add(Entity(id="ship", type="ship", label="little ship", phrase="a little pirate ship"))
    flag = world.add(Entity(id="flag", type="flag", label="red flag", phrase="a bright red flag", owner=hero.id))
    world.facts.update(hero=hero, friend=friend, ship=ship, flag=flag, hazard=hazard, rescue=rescue)

    hero.ally = friend.id
    friend.ally = hero.id
    ship.worn_by = hero.id

    world.say(f"{hero.id} and {friend.id} were two small pirates who loved each other's company.")
    world.say(f"They sailed a little ship toward {world.setting.place}, where {world.setting.sparkle} shone on the water.")
    world.say(f"{hero.id} treasured a {flag.label} on the ship, and {friend.id} liked to sing brave songs beside {hero.pronoun('object')}.")

    world.para()
    world.say(f"One {world.setting.tide} day, {hero.id} wanted to {hazard.verb}.")
    world.say(f"But the {hazard.risk} near the outlet looked tricky, and the tide could tug the ship toward the rocks.")
    hero.meters[hazard.id] = 1
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(f"{friend.id} frowned, then held up a hand and said, 'Let's be careful together.'")

    world.para()
    world.say(f"{hero.id} nodded and looked at {rescue.phrase}.")
    world.say(f"{friend.id} suggested, '{rescue.fix} so the ship can stay safe.'")
    world.say(f"{hero.id} trusted {friend.id}, and the two friends chose the safer way.")
    ship.memes["safe"] = 1
    ship.meters["safe"] = 1
    return world


def tell_story(world: World) -> World:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    ship = world.facts["ship"]
    hazard = world.facts["hazard"]
    rescue = world.facts["rescue"]

    world.say(f"{hero.id} and {friend.id} were not just crewmates; they were best friends.")
    world.say(f"That friendship made the day feel strong, even when the water at the outlet pulled fast.")

    world.para()
    world.say(f"Then the tide got bolder, and {hero.id}'s brave idea nearly sent the little ship into a mess.")
    world.say(f"{friend.id} grabbed the rope first, and {hero.id} held the other end so they would not drift apart.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Together they used {rescue.label}.")
    world.say(f"The ship stayed dry enough, the flag stayed bright, and the two friends laughed as they floated back to calm water.")
    world.say(f"At the outlet, the best treasure was not gold at all; it was how well {hero.id} and {friend.id} helped each other.")

    ship.memes["happy"] = 1
    hero.memes["happy"] = 1
    friend.memes["happy"] = 1
    return world


SETTINGS = {
    "harbor": Setting(place="the harbor outlet", tide="tide", sparkle="little sun-sparks"),
    "cove": Setting(place="the cove outlet", tide="high", sparkle="silver ripples"),
    "river": Setting(place="the river outlet", tide="low", sparkle="green flashes"),
}

HAZARDS = {
    "rocks": Hazard(id="rocks", verb="race toward the slippery rocks", mess="wet", risk="slippery rocks", zone="water", weather="windy"),
    "current": Hazard(id="current", verb="follow the quick current", mess="wet", risk="quick current", zone="water", weather="breezy"),
}

RESCUES = {
    "rope": Rescue(id="rope", label="a coil of rope", phrase="a coil of rope", fix="Tie the rope to the mast", covers="ship"),
    "anchor": Rescue(id="anchor", label="a small anchor", phrase="a small anchor", fix="Drop the small anchor", covers="ship"),
}

BOY_NAMES = ["Nico", "Finn", "Toby", "Milo", "Jace"]
GIRL_NAMES = ["Pia", "Mara", "Lina", "Tess", "Nora"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    rescue: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for hazard in HAZARDS:
            for rescue in RESCUES:
                combos.append((place, hazard, rescue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate friendship storyworld at the outlet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.rescue is None or c[2] == args.rescue)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, hazard, rescue = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES)
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in GIRL_NAMES if n != hero_name])
    return StoryParams(place=place, hazard=hazard, rescue=rescue, hero_name=hero_name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    hazard = HAZARDS[params.hazard]
    rescue = RESCUES[params.rescue]
    world = build_world(params.hero_name, params.friend_name, setting, hazard, rescue)
    tell_story(world)
    story = world.render()
    prompts = [
        f"Write a short pirate story about friendship at {setting.place}.",
        f"Tell a child-friendly tale where two pirate friends solve a problem with {rescue.label}.",
        f"Write a gentle adventure story about a ship near the outlet and a brave helping friend.",
    ]
    story_qa = [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {params.hero_name} and {params.friend_name}, two small pirate friends who helped each other.",
        ),
        QAItem(
            question=f"What problem did they face at the outlet?",
            answer=f"They worried that the ship could get wet and stuck near the slippery rocks or in the quick current.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {rescue.label} and worked together so the ship could stay safe.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a friendship?", answer="Friendship is when people care about each other, help each other, and want to stay together."),
        QAItem(question="What is an outlet in a story like this?", answer="An outlet is the place where water flows out toward the sea, like a river mouth or harbor mouth."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
hazard(H) :- threat(H).
rescue(R) :- fix(R).

compatible(P,H,R) :- place(P), hazard(H), rescue(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for h in HAZARDS:
        lines.append(asp.fact("threat", h))
    for r in RESCUES:
        lines.append(asp.fact("fix", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


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
    StoryParams(place="harbor", hazard="rocks", rescue="rope", hero_name="Nico", friend_name="Pia"),
    StoryParams(place="cove", hazard="current", rescue="anchor", hero_name="Finn", friend_name="Mara"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/3."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
