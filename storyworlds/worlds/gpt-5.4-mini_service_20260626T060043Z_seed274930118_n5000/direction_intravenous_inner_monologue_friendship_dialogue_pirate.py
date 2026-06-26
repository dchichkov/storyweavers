#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about choosing a safe direction, helping a sick
friend with an intravenous drip, and finding treasure in friendship instead of
greed.

Seed tale premise:
- A pirate crew is at sea.
- One friend is weak and needs an intravenous drip from the ship's kit.
- A storm and a risky direction tempt the captain to hurry on.
- The captain's inner monologue, friendship, and dialogue lead to a kinder
  choice: change direction, help the friend, and sail for a safe cove.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- explicit invalid choices raise StoryError
- inline ASP twin plus Python reasonableness gate
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Situation:
    id: str
    keyword: str
    event: str
    concern: str
    inner_thought: str
    stormy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    requires: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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


def _merge_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _merge_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if _meter(actor, "sick") >= THRESHOLD and actor.memes.get("comforted", 0.0) < THRESHOLD:
                sig = ("comfort", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _merge_meme(actor, "fear", -0.5)
                    _merge_meme(actor, "hope", 1.0)
                    changed = True
                    out.append(f"{actor.id} felt a little steadier.")
            if _meter(actor, "sick") >= THRESHOLD and _meme(actor, "friendship") >= THRESHOLD:
                sig = ("friendship", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _merge_meme(actor, "trust", 1.0)
                    changed = True
                    out.append(f"{actor.id} trusted the crew a bit more.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(setting: Setting, situation: Situation, remedy: Remedy) -> bool:
    if "intravenous" in situation.tags and "intravenous" not in remedy.helps:
        return False
    if "storm" in situation.tags and "safe_route" not in remedy.helps:
        return False
    return True


def _route_valid(route: str, situation: Situation) -> bool:
    if route == "north" and situation.stormy:
        return False
    return True


def select_remedy(situation: Situation) -> Remedy:
    for r in REMEDIES:
        if reasonableness_gate(SETTING, situation, r):
            return r
    raise StoryError("No reasonable remedy exists for this pirate tale.")


def _resolve_route(world: World, captain: Entity, friend: Entity, situation: Situation) -> str:
    if situation.stormy:
        return "south"
    return "east"


def tell(setting: Setting, situation: Situation, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    world.weather = "stormy" if situation.stormy else "calm"

    captain = world.add(Entity(
        id=hero_name, kind="character", type="captain", label="captain",
        meters={"resolve": 1.0}, memes={"duty": 1.0, "friendship": 1.0},
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type="pirate", label="matey",
        meters={"sick": 1.0, "weak": 1.0}, memes={"fear": 1.0, "friendship": 1.0},
    ))
    doctor = world.add(Entity(
        id="Doctor", kind="character", type="woman", label="ship doctor",
        memes={"kindness": 1.0},
    ))
    kit = world.add(Entity(
        id="Kit", type="thing", label="medicine kit",
        phrase="a small medicine kit with an intravenous drip",
        owner=hero_name, caretaker=doctor.id,
    ))

    world.say(f"{hero_name} was a bold pirate captain who loved the open sea.")
    world.say(f"{friend_name} was {hero_name}'s dear matey, and {hero_name} loved {friend_name} like family.")
    world.say(f"That morning, {friend_name} grew pale, and the ship doctor brought out {kit.phrase}.")
    world.say(f"{friend_name} needed the intravenous drip, and the crew had to choose a careful direction.")
    world.para()

    world.say(f"The waves slapped the hull, and the storm pulled at the sails.")
    world.say(f"In {hero_name}'s inner monologue, {situation.inner_thought}")
    world.say(f'“{situation.concern},” said the captain. “We must not be foolish.”')
    _merge_meme(captain, "worry", 1.0)
    _merge_meme(captain, "care", 1.0)
    _merge_meme(friend, "fear", 0.5)
    propagate(world)

    world.say(f"{hero_name} checked the map and picked a safer direction instead of chasing the wildest wind.")
    route = _resolve_route(world, captain, friend, situation)
    world.facts["route"] = route
    world.facts["situation"] = situation
    world.facts["captain"] = captain
    world.facts["friend"] = friend
    world.facts["doctor"] = doctor
    world.facts["kit"] = kit

    world.para()
    world.say(f'“{hero_name}, why are ye turning?” asked {friend_name}, voice small as a gull.')
    world.say(f'“Because yer more important than treasure,” {hero_name} said. “We sail {route} for the calm cove, and the doctor keeps the drip steady.”')
    world.say(f"{hero_name} felt a warm swell of friendship in the chest, like a lantern lit below deck.")
    _merge_meme(captain, "friendship", 1.0)
    _merge_meme(friend, "comforted", 1.0)
    _merge_meme(friend, "friendship", 1.0)
    propagate(world)

    world.para()
    remedy = select_remedy(situation)
    world.facts["remedy"] = remedy
    world.say(f"They {remedy.tail}.")
    world.say(f"The intravenous drip helped {friend_name} grow steadier, and the ship slid into a quiet cove.")
    world.say(f"{hero_name} looked at {friend_name} and grinned. “A true crew keeps its mates alive and laughing,” said the captain.")
    world.say(f"By sunset, the treasure of the day was not gold, but friendship, and the ship rested safely in the calm water.")

    world.facts["resolved"] = True
    return world


SETTING = Setting(place="the pirate ship", affords={"storm_route", "sickbay"})
SITUATIONS = {
    "storm": Situation(
        id="storm",
        keyword="direction",
        event="a storm",
        concern="We'll wreck the ship if we chase the wrong direction",
        inner_thought="The captain thought of the friend in the sick berth and chose care over haste.",
        stormy=True,
        tags={"storm", "direction"},
    ),
    "dock": Situation(
        id="dock",
        keyword="intravenous",
        event="a sick berth",
        concern="The friend needs the intravenous drip before any long voyage",
        inner_thought="The captain thought, 'A gentle tide is better than a bold fool's wind.'",
        stormy=False,
        tags={"intravenous", "friendship"},
    ),
}
REMEDIES = [
    Remedy(
        id="drip_and_detour",
        label="the drip and the detour",
        phrase="the drip and the detour",
        prep="follow the safer direction and keep the drip steady",
        tail="followed the safer direction and kept the drip steady",
        helps={"intravenous", "safe_route"},
    ),
    Remedy(
        id="safe_cove",
        label="the safe cove",
        phrase="the safe cove",
        prep="sail to the safe cove",
        tail="sailed to the safe cove",
        helps={"safe_route"},
    ),
]
GIRL_NAMES = ["Mara", "Nell", "Ruth", "Tess"]
BOY_NAMES = ["Finn", "Jory", "Puck", "Wes"]


@dataclass
class StoryParams:
    setting: str
    situation: str
    hero: str
    friend: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with direction, intravenous care, friendship, and dialogue.")
    ap.add_argument("--setting", choices=["ship"], default="ship")
    ap.add_argument("--situation", choices=list(SITUATIONS.keys()))
    ap.add_argument("--hero")
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
    situation = args.situation or rng.choice(list(SITUATIONS.keys()))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(setting="ship", situation=situation, hero=hero, friend=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sit = f["situation"]
    return [
        f'Write a pirate tale for a small child that includes "{sit.keyword}" and the word "intravenous".',
        f"Tell a pirate story where {f['captain'].id} chooses friendship over greed and speaks in dialogue on a stormy ship.",
        f"Write a short pirate story with inner monologue, friendship, and dialogue, ending with a safe direction and a calm cove.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap: Entity = f["captain"]
    friend: Entity = f["friend"]
    sit: Situation = f["situation"]
    return [
        QAItem(
            question=f"Why did {cap.id} change direction during the storm?",
            answer=f"{cap.id} changed direction because {friend.id} was sick and the storm made the old route too risky. The captain wanted to protect the crew and keep the intravenous drip safe.",
        ),
        QAItem(
            question=f"What did the crew help {friend.id} with?",
            answer=f"The crew helped {friend.id} with the intravenous drip from the medicine kit. That care made {friend.id} steadier before the ship sailed to the calm cove.",
        ),
        QAItem(
            question=f"How did {cap.id} show friendship in the story?",
            answer=f"{cap.id} showed friendship by choosing {friend.id}'s safety over treasure, talking kindly in dialogue, and steering toward a safer direction.",
        ),
        QAItem(
            question=f"What was the ending image of the pirate tale?",
            answer="The ending image showed the ship resting in quiet water, with the friend steadier, the storm behind them, and friendship shining brighter than gold.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a direction?",
            answer="A direction is a way to go, such as north, south, east, or west.",
        ),
        QAItem(
            question="What is an intravenous drip?",
            answer="An intravenous drip is a way for medicine or fluids to go slowly into a person's body through a small tube, usually in a hospital or clinic.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind even when things are hard.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is the words characters say out loud to each other.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    situation = SITUATIONS[params.situation]
    world = tell(SETTING, situation, params.hero, params.friend)
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


ASP_RULES = r"""
% A situation needs a safe route when it is stormy.
needs_safe_route(S) :- stormy(S).

% Intravenous care matters when the situation mentions intravenous.
needs_intravenous(S) :- mentions_intravenous(S).

% A remedy is reasonable if it covers the needed concern.
reasonable(R, S) :- needs_safe_route(S), helps(R, safe_route).
reasonable(R, S) :- needs_intravenous(S), helps(R, intravenous).

valid_story(S, R) :- situation(S), reasonable(R, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "ship"))
    for sid, s in SITUATIONS.items():
        lines.append(asp.fact("situation", sid))
        if s.stormy:
            lines.append(asp.fact("stormy", sid))
        if "intravenous" in s.tags:
            lines.append(asp.fact("mentions_intravenous", sid))
    for rid, r in enumerate(REMEDIES):
        lines.append(asp.fact("remedy", r.id))
        for h in sorted(r.helps):
            lines.append(asp.fact("helps", r.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for sid, s in SITUATIONS.items():
        for r in REMEDIES:
            if reasonableness_gate(SETTING, s, r):
                python_set.add((sid, r.id))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story pairs:")
        for sid, rid in vals:
            print(f"  {sid} -> {rid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(setting="ship", situation="storm", hero="Mara", friend="Finn"),
            StoryParams(setting="ship", situation="dock", hero="Puck", friend="Wes"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_story_params(args, random.Random(seed))
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
