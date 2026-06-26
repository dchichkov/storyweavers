#!/usr/bin/env python3
"""
storyworlds/worlds/verse_misunderstanding_space_adventure.py
============================================================

A tiny space-adventure story world about a misunderstood verse.

Premise:
- A small crew on a moon ship uses a verse to remember a route or task.
- One character misunderstands the verse and takes it too literally.
- The misunderstanding creates a small, concrete problem in the ship.
- The crew talks, checks the real meaning, and fixes the course together.

This world keeps the story grounded in physical meters and emotional memes:
- meters track ship position, fuel, light, noise, and object state
- memes track worry, confusion, trust, pride, and relief
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
# Core data model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def meter(self, name: str) -> float:
        return self.meters.get(name, 0.0)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    place: str
    course: str = "safe"
    meters: dict[str, float] = field(default_factory=lambda: {
        "fuel": 6.0,
        "distance": 0.0,
        "drift": 0.0,
        "signal": 1.0,
        "lights": 1.0,
        "damage": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "confusion": 0.0,
        "worry": 0.0,
        "trust": 0.0,
        "relief": 0.0,
        "pride": 0.0,
    })


@dataclass
class World:
    ship: Ship
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return World(
            ship=copy.deepcopy(self.ship),
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            fired=set(self.fired),
            facts=copy.deepcopy(self.facts),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    id: str
    place: str
    sky: str
    hazard: str
    detail: str


@dataclass
class Verse:
    id: str
    line: str
    meaning: str
    action: str
    hazard: str
    resolution: str


@dataclass
class Mission:
    id: str
    verb: str
    location: str
    reward: str
    effect: str
    risk: str
    recover: str
    keyword: str = "verse"


SETTINGS = {
    "moonport": Setting(
        id="moonport",
        place="the moonport dock",
        sky="silver dust",
        hazard="drift",
        detail="The dock lights blinked under a sky full of floating dust.",
    ),
    "asteroid_bay": Setting(
        id="asteroid_bay",
        place="the asteroid bay",
        sky="dark rock",
        hazard="echo",
        detail="The bay curved around quiet rocks that made every sound bounce.",
    ),
    "ring_station": Setting(
        id="ring_station",
        place="the ring station",
        sky="spinning lights",
        hazard="spin",
        detail="The station spun slowly, and the windows drew a bright circle around the crew.",
    ),
}

VERSES = {
    "left_right": Verse(
        id="left_right",
        line="Left for the lamp, right for the star, straight for the door that knows where we are.",
        meaning="The verse is a memory aid for choosing the correct corridor and heading.",
        action="follow the real direction signs",
        hazard="take every word literally",
        resolution="check the map instead of the rhyme alone",
    ),
    "soft_step": Verse(
        id="soft_step",
        line="Soft step, small step, keep the engines low; listen for the beacon and let the moon glow.",
        meaning="The verse reminds the crew to move quietly so they can hear the beacon.",
        action="lower the engine noise",
        hazard="make the ship too loud to hear the beacon",
        resolution="turn the engine down and listen together",
    ),
    "red_blue": Verse(
        id="red_blue",
        line="Red means pause, blue means go, gold means the path will help you know.",
        meaning="The verse is a code for ship lights and safe signals.",
        action="read the light signals correctly",
        hazard="mix up the light colors",
        resolution="match each light to its meaning",
    ),
}

MISSIONS = {
    "beacon": Mission(
        id="beacon",
        verb="find the beacon",
        location="the far side of the dock",
        reward="a steady signal",
        effect="the ship could point home",
        risk="a wrong turn would waste fuel",
        recover="the crew could still find the beacon if they listened carefully",
    ),
    "parcel": Mission(
        id="parcel",
        verb="deliver the parcel",
        location="the ring station market",
        reward="a warm thank-you from the station folk",
        effect="the parcel would reach the right bay",
        risk="the cargo door might stay shut too long",
        recover="they could open the right hatch once they understood the verse",
    ),
    "garden": Mission(
        id="garden",
        verb="reach the dome garden",
        location="the moon garden dome",
        reward="fresh leaves for supper",
        effect="the little plants would stay safe and watered",
        risk="a noisy approach would scare the garden drones",
        recover="they could slow down and use the verse properly",
    ),
}

CREW_NAMES = ["Nova", "Mira", "Kian", "Lio", "Aria", "Tess", "Rin", "Zed"]
CREW_TYPES = ["captain", "pilot", "engineer", "navigator"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    verse: str
    mission: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    verse = VERSES[params.verse]
    mission = MISSIONS[params.mission]
    ship = Ship(name="Tern", place=setting.place)
    world = World(ship=ship)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        label=params.hero,
        traits=["bright", "careful"],
        memes={"trust": 1.0, "confusion": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=params.friend_type,
        label=params.friend,
        traits=["quick", "eager"],
        memes={"trust": 1.0, "confusion": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    map_chip = world.add(Entity(
        id="map_chip",
        kind="thing",
        type="tool",
        label="map chip",
        phrase="a small map chip with the route on it",
        owner=hero.id,
        meters={"charge": 1.0},
    ))
    signal_lamp = world.add(Entity(
        id="signal_lamp",
        kind="thing",
        type="tool",
        label="signal lamp",
        phrase="a bright signal lamp",
        owner=friend.id,
        meters={"charge": 1.0},
    ))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="parcel",
        label="cargo crate",
        phrase="a little cargo crate",
        owner=hero.id,
        caretaker=friend.id,
        meters={"sealed": 1.0},
    ))

    world.facts.update(
        setting=setting,
        verse=verse,
        mission=mission,
        hero=hero,
        friend=friend,
        map_chip=map_chip,
        signal_lamp=signal_lamp,
        cargo=cargo,
    )
    return world


def confuse(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    verse = world.facts["verse"]
    mission = world.facts["mission"]
    ship = world.ship

    ship.memes["confusion"] += 1.0
    hero.memes["confusion"] += 1.0
    friend.memes["trust"] += 0.5
    world.say(
        f"On the {world.facts['setting'].place}, {hero.id} heard a verse: "
        f"“{verse.line}”"
    )
    world.say(
        f"{hero.id} thought the verse was a command to {verse.action}, "
        f"but it was really a reminder for the mission to {mission.verb}."
    )


def apply_misunderstanding(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    verse = world.facts["verse"]
    mission = world.facts["mission"]
    ship = world.ship

    sig = ("misunderstand", verse.id, mission.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    ship.meters["drift"] += 1.0
    ship.meters["fuel"] -= 1.0
    ship.memes["worry"] += 1.0
    hero.memes["worry"] += 1.0
    friend.memes["confusion"] += 1.0

    world.say(
        f"{hero.id} followed the wrong meaning, and the ship drifted away "
        f"from {mission.location}."
    )
    world.say(
        f"That mistake could waste fuel and make the mission harder, because "
        f"{mission.risk}."
    )


def correct_the_verse(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    verse = world.facts["verse"]
    mission = world.facts["mission"]
    ship = world.ship

    sig = ("correct", verse.id, mission.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    ship.memes["confusion"] = max(0.0, ship.memes["confusion"] - 1.0)
    ship.memes["trust"] += 1.0
    ship.memes["relief"] += 1.0
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1.0)
    hero.memes["relief"] += 1.0
    hero.memes["pride"] += 1.0
    friend.memes["confusion"] = max(0.0, friend.memes["confusion"] - 1.0)
    friend.memes["relief"] += 1.0
    ship.meters["drift"] = max(0.0, ship.meters["drift"] - 1.0)

    world.say(
        f"Then {friend.id} pointed to the map chip and smiled. "
        f"“The verse meant {verse.meaning}.”"
    )
    world.say(
        f"Together they chose to {verse.resolution}, and the Tern turned back "
        f"toward the right path."
    )
    world.say(
        f"By the end, {hero.id} knew the verse by heart, and the ship was "
        f"steady again."
    )


def tell(world: World) -> None:
    setting = world.facts["setting"]
    mission = world.facts["mission"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]

    world.say(
        f"At {setting.place}, the little ship Tern waited with its lights on."
    )
    world.say(setting.detail)
    world.say(
        f"{hero.id} and {friend.id} were ready to {mission.verb}. "
        f"They had {mission.reward} to look for."
    )
    world.para()
    confuse(world)
    apply_misunderstanding(world)
    world.para()
    world.say(
        f"{friend.id} did not laugh. {friend.pronoun().capitalize()} simply "
        f"showed the map chip and helped {hero.pronoun('object')} listen again."
    )
    correct_the_verse(world)


# ---------------------------------------------------------------------------
# Regenerable content helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    verse: Verse = f["verse"]
    mission: Mission = f["mission"]
    hero: Entity = f["hero"]
    return [
        f'Write a short space-adventure story for a child that includes the word "verse".',
        f"Tell a gentle story set at {setting.place} where {hero.id} misunderstands "
        f"a verse and the crew fixes the problem while trying to {mission.verb}.",
        f"Write a simple story about a space crew that hears a verse, makes a mistake, "
        f"and then learns the real meaning of the verse.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    verse: Verse = f["verse"]
    mission: Mission = f["mission"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    ship = world.ship
    return [
        QAItem(
            question=f"What did {hero.id} misunderstand at {setting.place}?",
            answer=(
                f"{hero.id} misunderstood a verse. {hero.pronoun().capitalize()} "
                f"thought it was a command, but it was really a reminder for the mission."
            ),
        ),
        QAItem(
            question=f"Why did the ship drift after {hero.id} followed the verse the wrong way?",
            answer=(
                f"The ship drifted because the wrong meaning sent the crew off course. "
                f"That used fuel and made the mission harder."
            ),
        ),
        QAItem(
            question=f"How did {friend.id} help after the misunderstanding?",
            answer=(
                f"{friend.id} showed the map chip, explained the real meaning of the verse, "
                f"and helped the crew turn back to the right path."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"At the end, the ship was steady again, the confusion was gone, and {hero.id} "
                f"understood the verse by heart."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    verse: Verse = f["verse"]
    mission: Mission = f["mission"]
    return [
        QAItem(
            question="What is a verse in this world?",
            answer=(
                "A verse is a short line of words that helps the crew remember what to do. "
                f"In this story, the verse was: “{verse.line}”."
            ),
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer=(
                "A misunderstanding happens when someone thinks something means one thing, "
                "but it really means something else."
            ),
        ),
        QAItem(
            question="Why do space crews use signals and maps?",
            answer=(
                "Space crews use signals and maps so they can stay safe, follow the right path, "
                "and avoid getting lost."
            ),
        ),
        QAItem(
            question=f"Where was the story set?",
            answer=f"The story was set at {setting.place}, where the crew could see {setting.sky}.",
        ),
        QAItem(
            question=f"What was the crew trying to do?",
            answer=(
                f"They were trying to {mission.verb}, which meant they needed to reach "
                f"{mission.location} safely."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"ship.course={world.ship.course}")
    lines.append(f"ship.place={world.ship.place}")
    lines.append(f"ship.meters={world.ship.meters}")
    lines.append(f"ship.memes={world.ship.memes}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when the verse can be misunderstood, then corrected.
misunderstood(V, M) :- verse(V), mission(M), hazard(V, H), triggers(M, H).
can_fix(V, M) :- verse(V), mission(M), resolution(V, R), repairs(M, R).
valid_story(S, V, M) :- setting(S), verse(V), mission(M), misunderstood(V, M), can_fix(V, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for vid, v in VERSES.items():
        lines.append(asp.fact("verse", vid))
        lines.append(asp.fact("hazard", vid, v.hazard))
        lines.append(asp.fact("resolution", vid, v.resolution))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("triggers", mid, m.risk.split(" ")[-2] if " " in m.risk else m.risk))
        lines.append(asp.fact("repairs", mid, "check the map instead of the rhyme alone") if mid == "beacon" else asp.fact("repairs", mid, "turn the engine down and listen together") if mid == "parcel" else asp.fact("repairs", mid, "match each light to its meaning"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for vid, verse in VERSES.items():
            for mid, mission in MISSIONS.items():
                if verse.hazard and mission.risk:
                    combos.append((sid, vid, mid))
    return combos


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def story_name_pool(gender: str) -> list[str]:
    return CREW_NAMES


def pick_crew(rng: random.Random) -> tuple[str, str, str, str]:
    hero = rng.choice(CREW_NAMES)
    friend = rng.choice([n for n in CREW_NAMES if n != hero])
    hero_type = rng.choice(CREW_TYPES)
    friend_type = rng.choice([t for t in CREW_TYPES if t != hero_type])
    return hero, hero_type, friend, friend_type


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about a misunderstood verse.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--verse", choices=VERSES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.verse is None or c[1] == args.verse)
              and (args.mission is None or c[2] == args.mission)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, verse, mission = rng.choice(sorted(combos))
    hero, hero_type, friend, friend_type = pick_crew(rng)
    if args.name:
        hero = args.name
    if args.friend:
        friend = args.friend
    return StoryParams(
        setting=setting,
        verse=verse,
        mission=mission,
        hero=hero,
        hero_type=hero_type,
        friend=friend,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="moonport", verse="left_right", mission="beacon", hero="Nova", hero_type="captain", friend="Mira", friend_type="navigator"),
    StoryParams(setting="asteroid_bay", verse="soft_step", mission="parcel", hero="Kian", hero_type="pilot", friend="Tess", friend_type="engineer"),
    StoryParams(setting="ring_station", verse="red_blue", mission="garden", hero="Aria", hero_type="navigator", friend="Rin", friend_type="captain"),
]


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
        print(sorted(set(asp.atoms(model, "valid_story"))))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
