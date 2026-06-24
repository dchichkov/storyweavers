#!/usr/bin/env python3
"""
storyworlds/worlds/television_shard_friendship_pirate_tale.py
==============================================================

A small story world for a pirate-tale friendship about a washed-ashore
television, a sharp shard, and a kind shared choice.

The source tale this world grows from:
---
On a windy island, a young pirate found a strange television that had washed up on
the sand. When he tapped it, a tiny shard of glass fell from the cracked screen.
His best friend warned him not to touch it, but the pirate wanted to keep the shiny
machine. Together they found a safer way: they carried the television home with a
cloth, wrapped the shard, and fixed the crack with care. In the end, the two friends
watched the sunset, happy that they had kept each other safe.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "sister"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "brother", "pirate"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the beach"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    type: str
    risky: bool = False
    shard_of: Optional[str] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    vessel: str
    seed: Optional[int] = None


SETTINGS = {
    "beach": Setting(place="the beach", affords={"wash_ashore"}),
    "cove": Setting(place="the cove", affords={"wash_ashore"}),
    "harbor": Setting(place="the harbor", affords={"wash_ashore"}),
    "deck": Setting(place="the deck", affords={"wash_ashore"}),
}

HERO_NAMES = ["Milo", "Nina", "Jory", "Luca", "Rina", "Pip"]
FRIEND_NAMES = ["Tess", "Bo", "Sail", "Mira", "Ned", "Kia"]
VESSELS = {
    "television": ObjectDef(
        id="television",
        label="television",
        phrase="a strange little television with a cracked screen",
        type="television",
        risky=True,
    ),
    "shard": ObjectDef(
        id="shard",
        label="shard",
        phrase="a sharp shard of glass",
        type="shard",
        risky=True,
        shard_of="television",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale friendship story world with a television and a shard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--vessel", choices=VESSELS)
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


def validate(params: StoryParams) -> None:
    if params.vessel not in VESSELS:
        raise StoryError("Unknown vessel.")
    if params.hero == params.friend:
        raise StoryError("The pirate and the friend must be different characters.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    vessel = args.vessel or rng.choice(list(VESSELS))
    params = StoryParams(place=place, hero=hero, friend=friend, vessel=vessel)
    validate(params)
    return params


def _set(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def predict_danger(world: World, vessel: Entity) -> bool:
    sim = world.copy()
    tv = sim.get(vessel.id)
    _set(tv, "touched")
    if vessel.type == "television":
        shard = sim.entities.get("shard")
        if shard:
            _set(shard, "loose")
    return True


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="pirate"))
    friend = world.add(Entity(id=params.friend, kind="character", type="pirate"))
    vessel_def = VESSELS[params.vessel]
    vessel = world.add(Entity(id=vessel_def.id, type=vessel_def.type, label=vessel_def.label, phrase=vessel_def.phrase))
    shard = world.add(Entity(id="shard", type="shard", label="shard", phrase="a sharp shard of glass", owner=vessel.id))
    world.facts.update(hero=hero, friend=friend, vessel=vessel, shard=shard, params=params)

    world.say(
        f"On {world.setting.place}, {hero.id} and {friend.id} were two young pirates who shared everything they found."
    )
    world.say(
        f"One day, they spied {vessel.phrase} washed up in the sand like treasure from a storm."
    )
    vessel.memes["shiny"] = 1.0
    hero.memes["want"] = 1.0
    friend.memes["care"] = 1.0

    world.para()
    world.say(f"{hero.id} wanted to keep the {vessel.label}, but {friend.id} noticed something sharp nearby.")
    shard.meters["loose"] = 1.0
    if predict_danger(world, vessel):
        world.say(f"A tiny {shard.label} had fallen from the cracked screen, and it could poke a hand.")

    world.para()
    friend.memes["warning"] = 1.0
    world.say(
        f'"Careful," said {friend.id}. "That {shard.label} is sharp, and the {vessel.label} needs gentle hands."'
    )
    hero.memes["stubborn"] = 1.0
    world.say(f"{hero.id} paused, then looked at {friend.id}. The two friends did not want anyone to get hurt.")

    world.para()
    cloth = world.add(Entity(id="cloth", type="cloth", label="cloth", phrase="a clean cloth"))
    cloth.owner = hero.id
    _set(hero, "helping")
    _set(friend, "helping")
    world.say(
        f"So they wrapped the {shard.label} in the {cloth.label} and carried the {vessel.label} together, one careful step at a time."
    )
    vessel.meters["safe"] = 1.0
    shard.meters["wrapped"] = 1.0
    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0

    world.say(
        f"At sunset, {hero.id} and {friend.id} sat side by side and watched the sky turn gold, happy that their friendship had kept the treasure safe."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a small child about {f["hero"].id}, {f["friend"].id}, a {f["vessel"].label}, and a {f["shard"].label}.',
        f"Tell a gentle friendship story where two pirates find {f['vessel'].phrase} and choose a safe way to carry it.",
        f'Write a simple story that includes the words "television" and "shard" and ends with friends helping each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, vessel, shard = f["hero"], f["friend"], f["vessel"], f["shard"]
    return [
        QAItem(
            question=f"Who found the {vessel.label} on the beach?",
            answer=f"{hero.id} and {friend.id} found it together while they were on {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {friend.id} warn {hero.id} about the {shard.label}?",
            answer=f"{friend.id} warned {hero.id} because the {shard.label} was sharp and could poke a hand.",
        ),
        QAItem(
            question=f"How did the friends keep the {vessel.label} safe?",
            answer=f"They wrapped the {shard.label} in a cloth and carried the {vessel.label} together with care.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} sitting together at sunset, happy that they had helped each other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shard?",
            answer="A shard is a sharp broken piece, like a small piece of glass or pottery.",
        ),
        QAItem(
            question="What is a television?",
            answer="A television is a screen that can show pictures and stories for people to watch.",
        ),
        QAItem(
            question="Why do friends help each other on a trip?",
            answer="Friends help each other because sharing care makes hard or risky jobs safer and kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
hero(H) :- character(H).
friend(F) :- character(F).
finds(H,V) :- hero(H), vessel(V).
sharp(S) :- shard(S).
warns(F,H) :- friend(F), hero(H), sharp(S).
safe_choice(H,F,V) :- hero(H), friend(F), vessel(V), careful(H,F,V).
resolved_story(H,F,V) :- safe_choice(H,F,V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("setting", p))
    for v in VESSELS.values():
        lines.append(asp.fact("vessel", v.id))
        if v.id == "television":
            lines.append(asp.fact("cracked", v.id))
        if v.id == "shard":
            lines.append(asp.fact("sharp", v.id))
    lines.append(asp.fact("careful", "pirate", "pirate", "television"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sharp/1. #show vessel/1."))
    if model is None:
        raise StoryError("ASP solver returned no model.")
    print("OK: ASP twin loads and solves.")
    return 0


def valid_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.vessel in VESSELS and params.hero != params.friend


CURATED = [
    StoryParams(place="beach", hero="Milo", friend="Tess", vessel="television"),
    StoryParams(place="cove", hero="Nina", friend="Bo", vessel="television"),
    StoryParams(place="harbor", hero="Jory", friend="Mira", vessel="television"),
]


def build_sample_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    if not valid_story(params):
        raise StoryError("The requested pirate friendship story is not valid.")
    return params


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show careful/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show vessel/1. #show sharp/1."))
        print("ASP model:")
        print(model)
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
                params = build_sample_args(args, random.Random(seed))
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
            header = f"### {p.hero} and {p.friend} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
