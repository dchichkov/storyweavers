#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/colander_art_room_bravery_bedtime_story.py
===============================================================================================================

A small bedtime-style storyworld about an art room, a colander, and a brave
choice before sleep.
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

STORY_THEME = "Bedtime Story"
ROOM_NAME = "the art room"


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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = ROOM_NAME
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"paint"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "colander"
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return any(g.region == region for g in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


THRESHOLD = 1.0


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("paint", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["paint"] = item.meters.get("paint", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got paint on it.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0.0) + 1
        out.append(f"That would mean extra cleaning for {caretaker.label}.")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("brave", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        out.append(f"{actor.id} took one brave breath.")
    return out


CAUSAL_RULES = [_r_soil, _r_worry, _r_brave]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting) -> str:
    return "The art room was quiet and warm, with one lamp glowing like a sleepy moon."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('traits', [])), 'gentle')} {hero.type} who loved the art room at bedtime."
    )


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because the tiny brushes felt like fireflies in {hero.pronoun('possessive')} hands."
    )


def show_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} kept a shiny {prize.label} nearby, because its round holes made pretty patterns when the light passed through."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One sleepy evening, {hero.id} and {hero.pronoun('possessive')} {parent.label} tiptoed into {world.setting.place}."
    )
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the new project felt a little scary in the quiet room."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.pronoun("possessive")} {parent.label} said softly.'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["nervous"] = hero.memes.get("nervous", 0.0) + 1
    world.say(f"{hero.id} held still for a moment, then tried to be brave enough to begin.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        region=gear.covers.pop() if len(gear.covers) == 1 else "",
        plural=gear.plural,
    ))
    g.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[g.id]
        return None
    world.say(
        f'{parent.id} smiled. "How about we {gear.prep} and then {activity.verb} together?"'
    )
    return g


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"{hero.id} took a brave breath, nodded, and went on."
    )
    world.say(
        f"Together they used the {gear.label}, and soon {hero.id} was {activity.gerund} while {prize.label} stayed clean and bright."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    hero.memes["traits"] = [trait]
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves(world, hero, activity)
    show_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear = offer(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


SETTINGS = {"art_room": Setting()}
ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a moon picture",
        gerund="painting moon-and-star pictures",
        rush="reach for the paintbrushes",
        mess="paint",
        soil="speckled with paint",
        zone={"hands", "torso"},
        keyword="colander",
        tags={"paint", "colander"},
    )
}
PRIZES = {
    "colander": Prize(
        label="colander",
        phrase="a shiny little colander",
        type="colander",
        region="hands",
        plural=False,
    )
}
GEAR = [
    Gear(
        id="apron",
        label="an old apron",
        covers={"torso"},
        guards={"paint"},
        prep="put on the old apron first",
        tail="wore the apron",
    ),
    Gear(
        id="towel",
        label="a soft towel",
        covers={"hands"},
        guards={"paint"},
        prep="lay out a soft towel under it",
        tail="spread the towel",
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Maya"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Eli", "Noah"]
TRAITS = ["brave", "gentle", "sleepy", "curious"]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short bedtime story in an art room that includes a colander and the word "{act.keyword}".',
        f"Tell a gentle story where {hero.id} finds courage to {act.verb} before bed.",
        f"Write a cozy story about bravery, paint, and a shiny colander under a warm lamp.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} in {world.setting.place}, and the idea felt a little scary at first.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because {prize.label} would get {act.soil} if {hero.id} painted without a better plan.",
        ),
        QAItem(
            question=f"How did the story become brave instead of messy?",
            answer=f"They used {gear.label if gear else 'a safer plan'} so {hero.id} could be brave and keep the {prize.label} clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a colander for?",
            answer="A colander is a bowl with holes in it. People use it to rinse food like pasta or berries so the water can drain away.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared, because you know it is worth trying.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
soiled(P) :- actor_paint(A), prize(P), in_zone(P, hands), not protected(P).
worry(C) :- caretaker(C), soiled(P).
brave(A) :- actor_paint(A), bravery(A).
valid_story :- setting(art_room), prize(colander), activity(paint).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "art_room"),
        asp.fact("activity", "paint"),
        asp.fact("prize", "colander"),
        asp.fact("in_zone", "colander", "hands"),
        asp.fact("caretaker", "Parent"),
        asp.fact("actor_paint", "hero"),
        asp.fact("bravery", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP gate recognizes the art-room colander story.")
        return 0
    print("MISMATCH: ASP gate did not recognize the story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: an art room, a colander, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(
        place="art_room",
        activity="paint",
        prize="colander",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams("art_room", "paint", "colander", "Mina", "girl", "mother", "brave")
        samples = [generate(params)]
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
