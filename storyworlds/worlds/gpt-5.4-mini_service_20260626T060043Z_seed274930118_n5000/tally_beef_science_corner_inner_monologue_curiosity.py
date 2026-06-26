#!/usr/bin/env python3
"""
A standalone story world about a child in the science corner who loves to tally,
follows curiosity, and finds a humorous safe way to work with beef broth.

The world is built as a tiny simulation with physical meters and emotional
memes. A child wants to do a messy science-corner activity; a caretaker sees the
risk to a treasured shirt; a compromise gear item makes the ending safe.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def inc_meter(self, key: str, amt: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amt

    def inc_meme(self, key: str, amt: float = 1.0) -> None:
        self.memes[key] = self.meme(key) + amt

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
    place: str = "the science corner"
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meter("wet") >= THRESHOLD:
                for item in world.worn_items(actor):
                    if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                        continue
                    sig = ("soil", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.inc_meter("wet", 1.0)
                    item.inc_meter("dirty", 1.0)
                    produced.append(f"{actor.id}'s {item.label} got wet and dirty.")
                    changed = True
            if actor.meter("wet") >= THRESHOLD:
                for item in world.entities.values():
                    if item.caretaker == actor.id and item.meter("dirty") >= THRESHOLD:
                        pass
    if narrate:
        for s in produced:
            world.say(s)


def activity_delight() -> str:
    return "The tallies looked like little fence posts, and even the broth seemed to be keeping score."


def predict_soil(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes),
                                "covers": set(v.covers)}) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    sim.get(actor.id).inc_meter(activity.mess, 1.0)
    prize = sim.entities[prize_id]
    if prize.region in activity.zone and not any(e.protective and prize.region in e.covers for e in sim.worn_items(sim.get(actor.id))):
        return True
    return False


def place_detail(setting: Setting) -> str:
    return "In the science corner, there was a little shelf, a tray of jars, and a chalkboard for tallies."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"Once there was a little {hero.type} named {hero.id}, and {hero.id} loved to tally things.")


def love(world: World, hero: Entity) -> None:
    hero.inc_meme("curiosity", 1.0)
    hero.inc_meme("joy", 1.0)
    world.say(f"{hero.pronoun().capitalize()} liked the science corner best, because every jar seemed to ask a question.")


def beef_setup(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id} found a bowl of beef broth set out for a counting game.")
    world.say(f"{hero.id} thought, in a small inner voice, 'If I tally every bubble, maybe the bowl will tell me a secret.'")
    prize.worn_by = hero.id
    world.say(f"But {hero.id} was wearing {hero.pronoun('possessive')} {prize.label}, and that shirt was meant to stay clean.")


def arrive(world: World, hero: Entity, caretaker: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} and {caretaker.label} came to {world.setting.place} to {activity.verb}.")
    world.say(place_detail(world.setting))


def warn(world: World, caretaker: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_soil(world, hero, activity, prize.id):
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"Mind the bowl," {caretaker.label} said. "It may splash your {prize.label} {activity.soil}."')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.inc_meme("curiosity", 1.0)
    world.say(f"{hero.id} wanted to peer closer anyway, for curiosity was knocking like a tiny drum.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def offer_gear(world: World, caretaker: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = next((g for g in GEAR if activity.mess in g.guards and prize.region in g.covers), None)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=caretaker.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if not predict_soil(world, hero, activity, prize.id):
        return None
    gear.worn_by = None
    del world.entities[gear.id]
    return gear_def


def accept(world: World, hero: Entity, caretaker: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.inc_meme("joy", 2.0)
    hero.memes["worry"] = 0.0
    world.say(f'{caretaker.label} smiled and said, "How about we put on {gear_def.label} first?"')
    world.say(f"{hero.id} laughed at that, because a science apron looked like a knight's cape for soup battles.")
    world.say(f"They {gear_def.tail}, and soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the bowl of beef broth was safely counted.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={}, memes={}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=parent_type, label="the teacher"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=caretaker.id,
        region=prize_cfg.region, plural=prize_cfg.plural
    ))
    hero.inc_meme("curiosity", 1.0)
    world.say(f"Once there was a little {trait} {hero.type} named {hero.id}, and {hero.id} loved to tally things.")
    world.say(f"{hero.id} had a curious heart and a funny thought: even a beef broth bowl could be counted one bubble at a time.")
    world.para()
    arrive(world, hero, caretaker, activity)
    beef_setup(world, hero, prize)
    warn(world, caretaker, hero, activity, prize)
    defy(world, hero, activity)
    world.para()
    gear_def = offer_gear(world, caretaker, hero, activity, prize)
    if gear_def:
        accept(world, hero, caretaker, activity, prize, gear_def)
    world.facts.update(hero=hero, caretaker=caretaker, prize=prize, activity=activity, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "science": Setting(place="the science corner", affords={"tally"}),
}

ACTIVITIES = {
    "tally": Activity(
        id="tally",
        verb="tally the bubbles in the beef broth",
        gerund="tallying bubbles in the beef broth",
        rush="lean over the bowl",
        mess="wet",
        soil="splashed wet",
        zone={"torso"},
        keyword="tally",
        tags={"tally", "beef"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean shirt",
        type="shirt",
        region="torso",
        genders={"girl", "boy"},
    )
}

GEAR = [
    Gear(
        id="apron",
        label="a science apron",
        covers={"torso"},
        guards={"wet"},
        prep="put on a science apron first",
        tail="put on the science apron and tiptoed back to the bowl",
    )
]

GIRL_NAMES = ["Mina", "Nia", "Tess", "Lina", "Ivy"]
BOY_NAMES = ["Eli", "Finn", "Owen", "Theo", "Ben"]
TRAITS = ["curious", "bright-eyed", "cheerful", "mischievous", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a folk-tale style story set in the science corner about {hero.id} and the word "tally".',
        f"Tell a child-friendly story where {hero.id} wants to {act.verb} but must keep {prize.label} clean.",
        f"Write a short story with curiosity and humor in the science corner, ending in a safe compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, prize, act = f["hero"], f["caretaker"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.id} was curious and kept thinking about every little bubble.",
        ),
        QAItem(
            question=f"Why did the teacher worry about {hero.id}'s {prize.label}?",
            answer=f"The teacher worried because the beef broth could splash and leave {prize.label} {act.soil}.",
        ),
        QAItem(
            question=f"What helped {hero.id} do the tallying safely?",
            answer=f"A science apron helped, because it covered the {prize.region} and kept the {prize.label} clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tallying?",
            answer="Tallying is counting things one by one and making marks so you can keep track.",
        ),
        QAItem(
            question="What is beef?",
            answer="Beef is meat from a cow. People may use beef in soup or broth, and it can smell strong while it cooks.",
        ),
        QAItem(
            question="Why do people wear aprons?",
            answer="People wear aprons to protect their clothes from splashes, stains, and messy bits.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} worn_by={e.worn_by}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale science-corner story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["teacher"])
    ap.add_argument("--name")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize does not fit that gender in this world.")
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent="teacher", trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(StoryParams(place="science", activity="tally", prize="shirt", name=n, gender=g, parent="teacher", trait=t))
                   for n, g, t in [("Nia", "girl", "curious"), ("Eli", "boy", "mischievous")]]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
