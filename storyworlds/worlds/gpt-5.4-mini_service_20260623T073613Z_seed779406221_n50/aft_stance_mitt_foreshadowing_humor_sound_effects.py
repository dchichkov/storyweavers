#!/usr/bin/env python3
"""
storyworlds/worlds/aft_stance_mitt_foreshadowing_humor_sound_effects.py
=======================================================================

A small pirate-tale storyworld with foreshadowing, humor, and sound effects.

Seed image:
---
A little pirate crew is playing on a ship. The aft deck is slick with sea spray.
One child wants to dash around in a silly stance with a mitt that is too big.
A grown-up notices clues that the mitt will slip, warns them, and offers a safer
game that keeps the pirate fun going.

Core beat:
- setup: pirate play on the ship
- foreshadowing: the aft deck, creaky rail, and a wobbly mitt hint at trouble
- humor: a silly stance and a comically oversized mitt
- sound effects: "creak", "thump", "splash", "whoosh"
- resolution: the crew switches to a steadier stance and a better mitt

The world is intentionally tiny and classical: one small domain, one tension,
one turn, one ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "mate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
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
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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
        self.weather: str = ""
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet",):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.id}'s {item.label} got {mess} and dirty.")
    return out


CAUSAL_RULES = [("soak", _r_soak)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sound(word: str) -> str:
    return {
        "creak": "Creeeak",
        "thump": "Thump",
        "splash": "Splash",
        "whoosh": "Whoosh",
        "clack": "Clack",
    }.get(word, word.capitalize())


def foreshadow(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"On the pirate ship, {hero.id} loved playing {activity.gerund} near the {world.setting.place}."
    )
    world.say(
        f"The aft deck gave a little {sound('creak')} whenever the sea rocked it, and a salty breeze made everything slippery."
    )
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like it was a treasure, even though it looked a bit too big."
    )


def humor_beat(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    hero.memes["silliness"] += 1
    world.say(
        f"{hero.id} struck a very grand pirate stance with the mitt, as if {hero.pronoun()} were guarding a gold whale."
    )
    world.say(
        f"{sound('thump')} {hero.id} hopped once, then twice, and the mitt made the pose even sillier."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, hero, activity, prize.id)
    world.facts["predicted_soil"] = activity.soil
    if pred["soiled"]:
        world.say(
            f'"That mitt will slip if you rush around the aft deck," {parent.id} said. '
            f'"You might end up {activity.soil}, and then I would have to clean it."'
        )
    else:
        world.say(
            f'"Easy there," {parent.id} said. "That deck is slick, and that mitt looks wobbly."'
        )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} wanted to dash anyway and took one piratey step toward the rail.")


def grab(conflicted: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    conflicted.say(
        f"{parent.id} caught {hero.pronoun('possessive')} hand before {hero.id} could slide aft."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        return None
    g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True,
                         covers=set(gear.covers), plural=gear.plural, owner=hero.id))
    g.worn_by = hero.id
    world.say(
        f'"How about we put on the {gear.label} and keep the fun?" {parent.id} said.'
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} nodded and grinned at the safer plan.")
    world.say(
        f"With {gear.label} on, {hero.id} could still play pirate, only now the stance was steady and the mitt stayed put."
    )
    world.say(
        f"{sound('clack')} {hero.id} tapped the deck, laughed, and the aft wind only ruffled {hero.pronoun('possessive')} {prize.label}."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, parent_name: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type="boy"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region,
                             plural=prize_cfg.plural))
    foreshadow(world, hero, parent, activity, prize)
    world.para()
    humor_beat(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    grab(world, parent, hero)
    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        accept(world, hero, parent, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


SETTINGS = {
    "ship": Setting(place="the aft deck", indoor=False, affords={"swing"}),
    "dock": Setting(place="the dock", indoor=False, affords={"swing"}),
}

ACTIVITIES = {
    "swing": Activity(
        id="swing",
        verb="practice a pirate swing",
        gerund="swinging in a pirate stance",
        rush="dash aft",
        mess="wet",
        soil="all wet",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="aft",
        tags={"aft", "stance", "mitt"},
    ),
}

PRIZES = {
    "mitt": Prize(label="mitt", phrase="a big blue mitt", type="mitt", region="feet", plural=False),
    "glove": Prize(label="glove", phrase="a striped glove-mitt", type="mitt", region="feet", plural=False),
}

GEAR = [
    Gear(id="sea_boots", label="sea boots", covers={"feet"}, guards={"wet"}, prep="put on sea boots", tail="wear sea boots", plural=True),
    Gear(id="grippy_mitt", label="a grippy mitt", covers={"feet"}, guards={"wet"}, prep="switch to a grippy mitt", tail="use the grippy mitt"),
]

GIRL_NAMES = ["Mara", "Nina", "Lina", "Tessa"]
BOY_NAMES = ["Owen", "Bram", "Finn", "Jace"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate story for a young child with foreshadowing, humor, and sound effects.',
        f"Tell a gentle pirate tale where {f['hero'].id} plays on {f['setting'].place} with a {f['prize'].label}, but the aft deck is slippery.",
        f'Write a story that uses the words "aft", "stance", and "mitt", and ends with a safer pirate pose.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(question=f"What did {hero.id} want to do on the ship?", answer=f"{hero.id} wanted to {activity.verb}, using {hero.pronoun('possessive')} {prize.label} like pirate gear."),
        QAItem(question=f"Why did {parent.id} worry about the aft deck?", answer=f"{parent.id} worried because the aft deck was slippery and {prize.label} looked wobbly, so a tumble could make {hero.id} {activity.soil}."),
        QAItem(question=f"What safer thing did they use at the end?", answer=f"They switched to {gear.label} and a steadier pirate stance, so the fun could keep going without a spill.") if gear else QAItem(question="What safer thing did they use at the end?", answer="They chose a steadier pirate pose and kept the fun careful."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does aft mean on a ship?", answer="Aft means the back part of a ship."),
        QAItem(question="What is a stance?", answer="A stance is the way someone stands or holds their body."),
        QAItem(question="What is a mitt?", answer="A mitt is a glove that covers your hand, and sometimes it is big and easy to spot."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["Mina", "Ruth", "Captain Nell"])
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero, params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with aft, stance, and mitt.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--parent")
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in s.affords:
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for gid, g in GEAR:
        pass
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,Pr) :- affords(P,A), splashes(A,R), worn_on(Pr,R).
"""


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(StoryParams(*c, hero="Mara", parent="Mina")) for c in valid_combos()]
    else:
        samples = []
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        print(s.story)
        if args.trace and s.world:
            print(dump_trace(s.world))
        if args.qa:
            print()
            print(format_qa(s))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
