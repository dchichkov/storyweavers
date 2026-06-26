#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/morphologic_fillet_wig_dim_reconciliation_friendship_superhero.py
====================================================================================================

A tiny superhero story world centered on friendship and reconciliation.

Seed-inspired premise:
- A brave superhero and a clever friend work together in a small city.
- They face a narrow, tricky rescue that calls for a morphologic gadget,
  a fillet-thin passage, and a wig-dim light.
- One rushed choice causes hurt feelings.
- A sincere apology and a shared plan restore trust and save the day.

This script follows the storyworld contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- exposes StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "mom"}
        masculine = {"boy", "man", "father", "dad"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


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
    risk: str
    zone: set[str]
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    mission: str
    gear: str
    name: str
    friend: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


SETTINGS = {
    "city_rooftop": Setting("the city rooftop", outdoor := True, affords={"rescue", "signal", "repair"}),
    "clock_tower": Setting("the old clock tower", outdoor := False, affords={"rescue", "signal"}),
    "harbor": Setting("the harbor dock", outdoor := True, affords={"rescue", "repair"}),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        verb="rescue the trapped kitten",
        gerund="rescuing the trapped kitten",
        rush="dash through the narrow gap",
        risk="the kitten could stay stuck",
        zone={"hands", "torso"},
        clue="a tiny mew from the dark gap",
        tags={"rescue", "friendship", "morphologic"},
    ),
    "signal": Mission(
        id="signal",
        verb="send a safe signal",
        gerund="watching the signal light blink",
        rush="run to the edge and wave",
        risk="nobody would know where to go",
        zone={"head", "hands"},
        clue="a faint blink in the dusk",
        tags={"signal", "wig-dim", "friendship"},
    ),
    "repair": Mission(
        id="repair",
        verb="repair the broken rooftop gate",
        gerund="repairing the broken rooftop gate",
        rush="grab the heavy wrench",
        risk="the gate might stay jammed",
        zone={"hands", "torso"},
        clue="a bent hinge and a loose bolt",
        tags={"repair", "fillet"},
    ),
}

GEAR = [
    Gear(
        id="morphologic_suit",
        label="a morphologic suit",
        covers={"hands", "torso"},
        helps={"rescue", "repair"},
        prep="pull on a morphologic suit",
        tail="put on the morphologic suit and tried again",
    ),
    Gear(
        id="fillet_line",
        label="a fillet-thin rescue line",
        covers={"hands"},
        helps={"rescue"},
        prep="thread a fillet-thin rescue line through the crack",
        tail="used the fillet-thin rescue line to slip through",
    ),
    Gear(
        id="wig_dim_lamp",
        label="a wig-dim lamp",
        covers={"head", "hands"},
        helps={"signal"},
        prep="switch on a wig-dim lamp",
        tail="switched on the wig-dim lamp and blinked the right code",
        plural=False,
    ),
]

HERO_NAMES = ["Nova", "Comet", "Spark", "Mira", "Jet", "Zara", "Pax", "Lyra"]
FRIEND_NAMES = ["Bee", "Tess", "Nico", "Rin", "Milo", "June", "Ollie", "Wren"]
TYPES = ["girl", "boy", "woman", "man"]
TRAITS = ["brave", "kind", "quick", "gentle", "cheerful", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.affords:
            for gear in GEAR:
                if mission_id in gear.helps:
                    combos.append((place, mission_id, gear.id))
    return combos


def reason_gate(place: str, mission_id: str, gear_id: str) -> None:
    mission = MISSIONS[mission_id]
    gear = next(g for g in GEAR if g.id == gear_id)
    if mission_id not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {SETTINGS[place].place} does not support {mission_id}.)")
    if mission_id not in gear.helps:
        raise StoryError(
            f"(No story: {gear.label} does not honestly help with {mission.verb}; "
            f"the fix would not change the risky part of the mission.)"
        )


def select_gear(mission_id: str) -> Gear:
    for gear in GEAR:
        if mission_id in gear.helps:
            return gear
    raise StoryError("(No story: no reasonable gear matches this mission.)")


def _do_mission(world: World, hero: Entity, friend: Entity, mission: Mission, narrate: bool = True) -> None:
    world.zone = set(mission.zone)
    hero.meters[mission.id] = hero.meters.get(mission.id, 0) + 1
    if mission.id == "signal":
        friend.meters["hope"] = friend.meters.get("hope", 0) + 1
    if narrate:
        world.say(f"{hero.id} worked on {mission.verb}.")
        world.say(mission.clue)


def predict_outcome(world: World, hero: Entity, friend: Entity, mission: Mission, gear: Gear) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), sim.get(friend.id), mission, narrate=False)
    return {
        "conflict": sim.get(friend.id).memes.get("hurt", 0) > 0,
        "success": mission.id in gear.helps,
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"{hero.id} was a {hero.type} superhero who loved helping the city.")
    world.say(f"{friend.id} was {friend.pronoun('object')} best friend and clever sidekick.")


def setup(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    world.say(f"Together, they had a habit of solving trouble before dinner.")
    world.say(f"That day, they saw {mission.clue} near {world.setting.place}.")
    world.say(f"They knew someone needed help, fast.")


def argue(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    hero.memes["rush"] = hero.memes.get("rush", 0) + 1
    friend.memes["hurt"] = friend.memes.get("hurt", 0) + 1
    world.say(
        f"{hero.id} wanted to {mission.rush} right away, but {friend.id} asked for one careful second."
    )
    world.say(
        f"{friend.id} said the plan should be slower, because {mission.risk}."
    )
    world.say(
        f"{hero.id} heard the warning and felt stung, as if the friendship light had gone dim."
    )


def reconcile(world: World, hero: Entity, friend: Entity, mission: Mission, gear: Gear) -> None:
    hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["hurt"] = max(0, friend.memes.get("hurt", 0) - 1)
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    world.say(f"{hero.id} stopped, took a breath, and said sorry for rushing ahead.")
    world.say(f"{hero.id} listened to {friend.id}'s idea and smiled.")
    world.say(f"Then they chose {gear.label} together because it matched the job.")
    world.say(f"{gear.prep.capitalize()}, {hero.id} and {friend.id} moved as a team.")


def resolve(world: World, hero: Entity, friend: Entity, mission: Mission, gear: Gear) -> None:
    if mission.id == "signal":
        world.say(f"{hero.id} and {friend.id} reached the edge and {gear.tail}.")
        world.say(f"The wink of light led the rescue crew straight to the right place.")
    elif mission.id == "repair":
        world.say(f"{hero.id} and {friend.id} fixed the gate by working carefully side by side.")
        world.say(f"When the bolt clicked in, the rooftop felt safe again.")
    else:
        world.say(f"{hero.id} and {friend.id} slipped through the narrow spot and found the kitten.")
        world.say(f"The kitten popped free, landed in {friend.id}'s arms, and purred.")
    world.say(f"By the end, the city was safer, and their friendship felt bright again.")


def tell(setting: Setting, mission: Mission, gear: Gear,
         hero_name: str = "Nova", friend_name: str = "Bee",
         hero_type: str = "girl", friend_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    intro_gear = world.add(Entity(id=gear.id, type="thing", label=gear.label, owner=hero.id))
    intro_gear.worn_by = None

    introduce(world, hero, friend)
    world.para()
    setup(world, hero, friend, mission)
    world.para()
    argue(world, hero, friend, mission)
    reconcile(world, hero, friend, mission, gear)
    world.para()
    resolve(world, hero, friend, mission, gear)

    world.facts.update(
        hero=hero,
        friend=friend,
        mission=mission,
        gear=gear,
        setting=setting,
        conflict=True,
        resolved=True,
    )
    return world


@dataclass
class StoryParams:
    place: str
    mission: str
    gear: str
    name: str
    friend: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly superhero story that includes the words "morphologic", "fillet", and "wig-dim".',
        f"Tell a story about {f['hero'].id} and {f['friend'].id} who disagree during a rescue, then make up and work together.",
        f"Write a short superhero friendship story set at {f['setting'].place} with a clear apology and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    mission: Mission = f["mission"]
    gear: Gear = f["gear"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who are the two heroes in the story?",
            answer=f"The story is about {hero.id} and {friend.id}, who work together as friends.",
        ),
        QAItem(
            question=f"What did they need to do at {setting.place}?",
            answer=f"They needed to {mission.verb}, and that was tricky because {mission.risk}.",
        ),
        QAItem(
            question=f"What helped them solve the problem?",
            answer=f"{gear.label.capitalize()} helped them, because it matched the kind of rescue they were doing.",
        ),
        QAItem(
            question=f"What fixed their argument?",
            answer=f"{hero.id} apologized, listened to {friend.id}, and chose a shared plan instead of rushing alone.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the rescue finished, the problem solved, and the friendship feeling bright again.",
        ),
    ]


KNOWLEDGE = {
    "morphologic": [
        QAItem(
            question="What does morphologic mean in a superhero story?",
            answer="In a superhero story, morphologic can mean something that changes shape or fit to match the job.",
        )
    ],
    "fillet": [
        QAItem(
            question="What does fillet mean here?",
            answer="Here, fillet means very thin and narrow, like a strip that can fit through a small crack.",
        )
    ],
    "wig-dim": [
        QAItem(
            question="What does wig-dim mean here?",
            answer="Here, wig-dim means a light or signal that can be turned down low and blinked carefully.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and try to be kind after a mistake.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, forgive each other, and come back together peacefully.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mission"].tags)
    tags.update({"friendship", "reconciliation"})
    out: list[QAItem] = []
    for tag in ["morphologic", "fillet", "wig-dim", "friendship", "reconciliation"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Mission, Gear) :- place(Place), mission(Mission), gear(Gear),
                                    supports(Place, Mission), helps(Gear, Mission).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(setting.affords):
            lines.append(asp.fact("supports", pid, m))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.helps):
            lines.append(asp.fact("helps", gear.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero friendship story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--friend-type", choices=TYPES)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.gear is None or c[2] == args.gear)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, gear = rng.choice(filtered)
    hero_type = args.hero_type or rng.choice(TYPES)
    friend_type = args.friend_type or rng.choice(TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    reason_gate(place, mission, gear)
    return StoryParams(place, mission, gear, name, friend, hero_type, friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], next(g for g in GEAR if g.id == params.gear),
                 params.name, params.friend, params.hero_type, params.friend_type)
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
    StoryParams("city_rooftop", "rescue", "morphologic_suit", "Nova", "Bee", "girl", "girl"),
    StoryParams("clock_tower", "signal", "wig_dim_lamp", "Spark", "Rin", "boy", "girl"),
    StoryParams("harbor", "repair", "morphologic_suit", "Lyra", "Milo", "girl", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
