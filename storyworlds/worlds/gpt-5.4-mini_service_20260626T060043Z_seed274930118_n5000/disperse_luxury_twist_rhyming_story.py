#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/disperse_luxury_twist_rhyming_story.py
===============================================================================================================

A small rhyming storyworld about a child who loves luxury things, a windy
problem that can disperse them, and a Twist that turns the day around.

Seed tale sketch:
---
Mina loved fancy, luxurious things: satin bows, shiny cups, and a soft gold cape.
One bright day at a garden tea, she wanted to send her pearl confetti into the air.
But the breeze could disperse it all over the path, which would make a mess and
leave the fancy table looking bare.

Her mother saw the trouble and offered a twist: braid the ribbon into a little
garland before they toss the confetti. Mina tried the twist, and the garland held
the sparkle close. The confetti still danced, but it stayed together long enough
to make a happy, rhyming shower.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"twirl", "parade"}),
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"twirl", "breeze"}),
    "parlor": Setting(place="the parlor", indoor=True, affords={"twirl"}),
}

ACTIVITIES = {
    "breeze": Activity(
        id="breeze",
        verb="send the pearls into the breeze",
        gerund="sending pearls into the breeze",
        rush="run toward the open gate",
        mess="scatter",
        soil="scattered everywhere",
        zone={"ground", "table"},
        weather="windy",
        keyword="disperse",
        tags={"disperse", "wind"},
    ),
    "twirl": Activity(
        id="twirl",
        verb="twirl the ribbon garland",
        gerund="twirling a ribbon garland",
        rush="spin too fast",
        mess="tangle",
        soil="all tangled up",
        zone={"hands"},
        weather="",
        keyword="Twist",
        tags={"twist", "ribbon"},
    ),
    "parade": Activity(
        id="parade",
        verb="march in the fancy parade",
        gerund="marching in the fancy parade",
        rush="dash down the path",
        mess="scatter",
        soil="lost in the path",
        zone={"ground", "hands"},
        weather="windy",
        keyword="luxury",
        tags={"luxury", "wind"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a soft gold cape",
        type="cape",
        region="torso",
    ),
    "bow": Prize(
        label="bow",
        phrase="a satin bow",
        type="bow",
        region="head",
    ),
    "cup": Prize(
        label="cup",
        phrase="a shiny pearl cup",
        type="cup",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="ribbon",
        label="a ribbon twist",
        covers={"hands"},
        guards={"scatter", "tangle"},
        prep="make a ribbon twist first",
        tail="made a ribbon twist and held the pearls close",
    ),
    Gear(
        id="basket",
        label="a woven basket lid",
        covers={"ground", "hands"},
        guards={"scatter"},
        prep="cover the tray with a basket lid first",
        tail="covered the tray and kept the pearls together",
        plural=False,
    ),
    Gear(
        id="clip",
        label="a silver clip",
        covers={"head"},
        guards={"tangle"},
        prep="clip the bow with a silver clip first",
        tail="clipped the bow and kept it neat",
    ),
]


GIRL_NAMES = ["Mina", "Lila", "Nora", "Zia", "Pia", "Ruby"]
BOY_NAMES = ["Theo", "Luca", "Finn", "Milo", "Noah", "Ezra"]
TRAITS = ["bright", "gentle", "cheery", "curious", "spry"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or activity.id in {"breeze", "parade"}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.m(self_key(activity.mess)) + 1
    actor.memes["joy"] = actor.e("joy") + 1
    if narrate:
        propagate(world)


def self_key(key: str) -> str:
    return key


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    for actor in world.characters():
        if actor.m("scatter") >= THRESHOLD:
            for item in world.worn_items(actor):
                if item.protective:
                    continue
                if item.region in world.zone and not world.covered(actor, item.region):
                    sig = ("mess", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["dirty"] = item.m("dirty") + 1
                    lines.append(f"The fancy thing got messy in the breeze.")
        if actor.m("tangle") >= THRESHOLD and actor.memes.get("twist_needed", 0) < THRESHOLD:
            actor.memes["twist_needed"] = 1
            lines.append(f"The ribbon wanted a twist to make it right.")
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.m("dirty") >= THRESHOLD}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.memes if False) if False else hero.type} with a taste for sparkle and shine.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"joy": 0.0, "love": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom", memes={"worry": 0.0}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"dirty": 0.0},
    ))

    world.say(f"{hero.id} loved things that gleamed, things that shimmered, things rich and sublime.")
    world.say(f"{hero.id} loved luxury treats that sparkled like treasure in rhyme.")
    world.say(f"Then {hero.id} wore {prize.phrase}, soft as a cloud and fine.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f"The breeze could {activity.keyword.lower()} and make the fancy bits wander and roam.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} saw the risk and spoke in a hum:")
    world.say(f"\"If you do that now, your {prize.label} may go {activity.soil}.\"")
    hero.memes["worry"] = 0.0
    hero.memes["defiance"] = 1.0
    predict_mess(world, hero, activity, prize.id)
    _do_activity(world, hero, activity, narrate=True)

    world.para()
    if activity.id == "twirl":
        world.say(f"{hero.id} frowned, then found the heart of the twist.")
    else:
        world.say(f"{hero.id} pouted, but the worry felt heavy and numb.")
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No sensible Twist could keep this luxury safe.")
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        meters={},
    ))
    gear.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} offered {gear_def.prep}.")
    world.say(f"\"Try the Twist,\" she said, \"and keep the sparkle in sight.\"")
    hero.memes["joy"] = 2.0
    hero.memes["love"] = 1.0
    world.say(f"{hero.id} smiled, took the twist, and held the prize just right.")
    world.say(f"Soon {hero.id} was {activity.gerund}, and the luxury gleam stayed bright.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear_def, resolved=True)
    return world


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
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a rhyming story for a young child about "{act.keyword}" and a little bit of "{prize.label}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb}, but a parent worries the luxury item will go away.",
        f'Create a short, musical story that includes the words "{act.keyword}" and "luxury" and ends with a Twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    prize = f["prize"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because the day felt bright and shiny.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label} worry about the {prize.label}?",
            answer=f"She worried because the breeze could {act.keyword.lower()} it and leave it {act.soil}.",
        ),
        QAItem(
            question=f"What Twist helped the story end well?",
            answer=f"They used {gear.label} so the fancy little {prize.label} could stay together and neat.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm, because the luxury sparkle stayed close while they played.",
        ),
    ]


KNOWLEDGE = {
    "disperse": [("What does it mean to disperse something?",
                  "To disperse something means to spread it out so it goes in many directions.")],
    "luxury": [("What does luxury mean?",
                "Luxury means something is extra nice, fancy, soft, or special.")],
    "twist": [("What is a twist?",
               "A twist is a turning motion, like twisting ribbon or turning a knob.")],
    "wind": [("What can wind do?",
               "Wind can push light things around, make leaves dance, and scatter little pieces.")],
    "ribbon": [("What is ribbon used for?",
                "Ribbon is a long, thin strip used to tie, wrap, or decorate things.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["disperse", "luxury", "twist", "wind", "ribbon"]:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="twirl", prize="cape", name="Mina", gender="girl", parent="mother", trait="bright"),
    StoryParams(place="courtyard", activity="breeze", prize="cup", name="Theo", gender="boy", parent="father", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.keyword} would not reasonably risk the {prize.label} in a way the Twist can fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about luxury, disperse, and a Twist.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:8} {prize:8}  [{', '.join(genders)}]")
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
