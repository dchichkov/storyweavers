#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/matzo_termite_teamwork_sharing_superhero_story.py
=============================================================================================================================

A small superhero-style story world about teamwork, sharing, matzo, and a termite.

The seed tale behind the world:
- A young superhero wants to help fix a broken treehouse lookout.
- A termite has chewed part of the wood, so the team must work together.
- They share tools, share snack matzo, and use a clever plan instead of a fight.
- The ending should show the lookout restored and everyone calm, fed, and proud.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of asp helper inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | creature
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "creature":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    threat: str
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class World:
    setting: Setting

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in getattr(g, "covers", set()) for g in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


REGIONS = {"hands", "torso", "head", "feet"}


def _r_termite_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("termite_alert", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.label != "wooden lookout":
                continue
            if "wood" not in world.zone:
                continue
            sig = ("damage", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["broken"] = item.meters.get("broken", 0.0) + 1.0
            out.append("The wooden lookout creaked and split a little more.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("teamwork", 0.0) < THRESHOLD:
            continue
        sig = ("teamwork", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1.0
        out.append(f"{actor.id} felt braver because the whole team was helping.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    matzo = world.entities.get("matzo")
    termite = world.entities.get("termite")
    hero = world.entities.get("hero")
    if not matzo or not termite or not hero:
        return out
    if hero.memes.get("sharing", 0.0) < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    termite.memes["calm"] = termite.memes.get("calm", 0.0) + 1.0
    out.append("They shared a square of matzo, and the tiny termite stopped fussing.")
    return out


CAUSAL_RULES = [
    Rule(name="termite_damage", apply=_r_termite_damage),
    Rule(name="teamwork", apply=_r_teamwork),
    Rule(name="sharing", apply=_r_sharing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mission_at_risk(mission: Mission) -> bool:
    return "wood" in mission.zone


def choose_gear(mission: Mission) -> Optional[Gear]:
    for gear in GEAR:
        if mission.threat in gear.guards:
            return gear
    return None


def predict(world: World, actor: Entity, mission: Mission) -> dict:
    sim = world.copy()
    actor2 = sim.get(actor.id)
    actor2.memes["termite_alert"] = 1.0
    actor2.meters["action"] = 1.0
    sim.zone = set(mission.zone)
    propagate(sim, narrate=False)
    lookout = sim.entities.get("lookout")
    return {"broken": bool(lookout and lookout.meters.get("broken", 0.0) >= THRESHOLD)}


def introduce(world: World, hero: Entity, sidekick: Entity, termite: Entity) -> None:
    world.say(
        f"{hero.id} was a small superhero with a bright cape and a brave heart. "
        f"{sidekick.id} was {hero.pronoun('possessive')} trusty teammate, and the tiny termite "
        f"lived near the old clubhouse."
    )


def setup_scene(world: World, hero: Entity, mission: Mission) -> None:
    world.say(
        f"One sunny afternoon, the team flew to {world.setting.place} to check the wooden lookout."
    )
    world.say(
        f"They loved {mission.gerund}, because every good rescue started with a calm plan."
    )


def warn(world: World, hero: Entity, mission: Mission) -> bool:
    pred = predict(world, hero, mission)
    if not pred["broken"]:
        return False
    world.facts["predicted_broken"] = True
    world.say(
        f'"If we rush in, the {mission.label if hasattr(mission, "label") else "lookout"} could fall apart," '
        f"{hero.id} said."
    )
    return True


def team_thinks(world: World, hero: Entity, sidekick: Entity, mission: Mission) -> None:
    hero.memes["termite_alert"] = 1.0
    sidekick.memes["teamwork"] = 1.0
    hero.memes["teamwork"] = 1.0
    world.say(
        f"{sidekick.id} nodded. Together they studied the chewed boards and counted the missing pieces."
    )
    world.say(
        f"{hero.id} wanted to {mission.rush}, but {sidekick.id} reminded {hero.pronoun('object')} to slow down."
    )


def offer_sharing(world: World, hero: Entity, termite: Entity, matzo: Entity) -> None:
    hero.memes["sharing"] = 1.0
    termite.memes["hungry"] = 1.0
    world.say(
        f"Then {hero.id} broke the {matzo.label} into little squares and shared one with the termite."
    )


def fix(world: World, hero: Entity, sidekick: Entity, mission: Mission, gear: Gear) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    sidekick.memes["hope"] = sidekick.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{hero.id} and {sidekick.id} put on {gear.label} and used {gear.prep}."
    )
    world.zone = set(mission.zone)
    propagate(world, narrate=True)
    world.say(
        f"Board by board, they mended the lookout, and the termite crawled safely to a bark pile."
    )


def ending(world: World, hero: Entity, sidekick: Entity, termite: Entity) -> None:
    world.say(
        f"At the end, the lookout stood straight again, {hero.id}'s cape fluttered in the breeze, "
        f"and the team sat together sharing the last piece of matzo while the termite stayed busy on its bark pile."
    )


SETTINGS = {
    "clubhouse": Setting(place="the clubhouse", indoor=False, affords={"repair"}),
    "park": Setting(place="the park", indoor=False, affords={"repair"}),
    "rooftop": Setting(place="the rooftop", indoor=False, affords={"repair"}),
}

MISSIONS = {
    "repair": Mission(
        id="repair",
        verb="fix the termite-chewed lookout",
        gerund="repairing the lookout",
        rush="dash up the ladder",
        threat="wood",
        danger="the lookout could crack",
        zone={"wood"},
        keyword="teamwork",
        tags={"teamwork", "sharing", "termite", "matzo"},
    )
}

GEAR = [
    Gear(
        id="toolbelt",
        label="a toolbelt",
        covers={"torso"},
        guards={"wood"},
        prep="share the hammer, the nails, and the shiny screwdriver",
        tail="finished the job together",
    ),
    Gear(
        id="gloves",
        label="soft work gloves",
        covers={"hands"},
        guards={"wood"},
        prep="take turns holding the boards and passing the nails",
        tail="kept helping side by side",
    ),
]

CHARACTER_TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    sidekick: str
    gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Maya", "Lina", "Ruby", "Tess", "Nora", "Ivy"]
BOY_NAMES = ["Max", "Eli", "Finn", "Theo", "Jude", "Sam"]
SIDEKICKS = ["Bolt", "Pixel", "Comet", "Spark", "Nova", "Echo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mission_id) for place, s in SETTINGS.items() for mission_id in s.affords if mission_id in MISSIONS]


def reason_invalid(place: str, mission: str) -> str:
    return f"(No story: the mission '{mission}' does not fit the setting '{place}' in this world.)"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mission = MISSIONS[params.mission]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label="hero",
        meters={},
        memes={},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick,
        kind="character",
        type="friend",
        label="sidekick",
        meters={},
        memes={},
    ))
    termite = world.add(Entity(
        id="termite",
        kind="creature",
        type="termite",
        label="termite",
        meters={"tiny": 1.0},
        memes={"hungry": 1.0},
    ))
    matzo = world.add(Entity(
        id="matzo",
        kind="thing",
        type="snack",
        label="matzo",
        phrase="a crispy square of matzo",
        owner=hero.id,
    ))
    lookout = world.add(Entity(
        id="lookout",
        kind="thing",
        type="structure",
        label="wooden lookout",
        phrase="a high wooden lookout",
        caretaker=hero.id,
        meters={"broken": 0.0},
    ))

    introduce(world, hero, sidekick, termite)
    world.para()
    setup_scene(world, hero, mission)
    if not warn(world, hero, mission):
        world.say(f"But {hero.id} still knew the lookout needed care.")
    team_thinks(world, hero, sidekick, mission)
    offer_sharing(world, hero, termite, matzo)
    gear = choose_gear(mission)
    if gear is None:
        raise StoryError("No reasonable gear exists for this mission.")
    fix(world, hero, sidekick, mission, gear)
    ending(world, hero, sidekick, termite)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        termite=termite,
        matzo=matzo,
        lookout=lookout,
        mission=mission,
        gear=gear,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    return [
        f'Write a short superhero story for a young child about teamwork and sharing that includes the word "matzo".',
        f"Tell a gentle rescue story where {hero.id} and {f['sidekick'].id} use teamwork to {mission.verb} with a termite nearby.",
        f"Write a simple story about a superhero team who shares matzo, solves a small termite problem, and ends with a happy repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    termite = f["termite"]
    mission = f["mission"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What problem did {hero.id} and {sidekick.id} try to solve?",
            answer=f"They tried to solve the termite damage and fix the wooden lookout before it could crack more.",
        ),
        QAItem(
            question=f"Why did {hero.id} share matzo with the termite?",
            answer=f"{hero.id} shared matzo to calm the termite down and make the rescue safer and kinder.",
        ),
        QAItem(
            question=f"What helped the team finish the job?",
            answer=f"Teamwork and {gear.label} helped them share tools, fix the lookout, and keep helping side by side.",
        ),
        QAItem(
            question=f"What happened to the termite at the end?",
            answer="The termite was safe on its bark pile and no longer chewing the lookout.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is matzo?",
            answer="Matzo is a crisp, flat bread often eaten as a simple snack.",
        ),
        QAItem(
            question="What is a termite?",
            answer="A termite is a tiny insect that likes to chew wood.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other finish a job.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else so everyone can enjoy it.",
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("threat", mid, m.threat))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for gid, g in {g.id: g for g in GEAR}.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Mission) :- affords(Place,Mission), mission(Mission).
needs_gear(Mission) :- zone(Mission,wood).
compatible(G,Mission) :- gear(G), needs_gear(Mission), guards(G,wood).
has_fix(Mission) :- compatible(_,Mission).
valid_story(Place,Mission) :- valid(Place,Mission), has_fix(Mission).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about teamwork, sharing, matzo, and a termite.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gender", choices=CHARACTER_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if args.place or args.mission:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.mission is None or c[1] == args.mission)]
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    place, mission = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(CHARACTER_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=place, mission=mission, name=name, sidekick=sidekick, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="clubhouse", mission="repair", name="Maya", sidekick="Bolt", gender="girl"),
    StoryParams(place="park", mission="repair", name="Max", sidekick="Spark", gender="boy"),
    StoryParams(place="rooftop", mission="repair", name="Nora", sidekick="Nova", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mission in combos:
            print(f"  {place:10} {mission}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
