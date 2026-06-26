#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/slave_proximity_dryer_riverbank_teamwork_transformation_curiosity.py
=================================================================================================

A small superhero-style storyworld set at a riverbank.

Seed story sketch:
---
A curious young superhero notices that a muddy cape is still too wet to use after
a riverbank rescue. A teammate spots a dryer in a nearby boathouse, but the
machine only helps if it is brought close enough to the cape. The two heroes use
teamwork to move the dryer, dry the cape, and finish the day feeling transformed
and proud.

This world keeps the premise tight:
- curiosity reveals the problem and the tool
- proximity matters because the dryer only works when moved close
- teamwork solves the problem
- transformation is the emotional/physical turn when the wet gear becomes ready
  again

The word "slave" is included in the seed vocabulary via a harmless in-world
name for a maintenance label on the old dryer unit, but the story itself stays
focused on rescue, teamwork, and change.
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

SETTING_NAME = "the riverbank"


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = SETTING_NAME
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    hero_name: str
    hero_gender: str
    sidekick_name: str
    parent_name: str
    activity: str
    prize: str
    seed: Optional[int] = None


SETTINGS = {"riverbank": Setting(place=SETTING_NAME, affords={"rescue", "splash"})}

ACTIVITIES = {
    "rescue": Activity(
        id="rescue",
        verb="help the ducklings across the water",
        gerund="helping the ducklings across the water",
        rush="dash to the water",
        mess="wet",
        soil="soaked through",
        zone={"torso", "legs"},
        keyword="teamwork",
        tags={"teamwork", "curiosity", "transformation", "wet"},
    ),
    "splash": Activity(
        id="splash",
        verb="chase the floating reeds",
        gerund="chasing the floating reeds",
        rush="run along the bank",
        mess="wet",
        soil="sprayed with river water",
        zone={"legs", "feet"},
        keyword="curiosity",
        tags={"curiosity", "teamwork", "wet"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a bright blue cape",
        type="cape",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="a pair of red boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="dryer",
        label="the old dryer",
        covers={"torso", "legs", "feet"},
        guards={"wet"},
        prep="pull the old dryer close to the cape",
        tail="rolled the dryer closer and let the warm air do its work",
    )
]

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Tara", "Zia"]
BOY_NAMES = ["Ezra", "Finn", "Kai", "Leo", "Owen"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld at a riverbank.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("That activity would not honestly threaten that prize, so the story would not have a real turn.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid combination matches the requested options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(["Pip", "Nova", "Dash", "Bee"])
    parent = args.parent or rng.choice(["Aunt", "Uncle", "Coach"])
    return StoryParams(
        hero_name=name,
        hero_gender=gender,
        sidekick_name=sidekick,
        parent_name=parent,
        activity=activity,
        prize=prize,
    )


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1.0


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["riverbank"])
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="friend"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="adult"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        plural=prize_cfg.plural,
    ))
    dryer = world.add(Entity(
        id="dryer",
        type="machine",
        label="dryer",
        phrase="an old riverbank dryer with a fading label",
        tags={"dryer", "slave", "proximity"},
    ))

    hero.memes["curiosity"] = 1.0
    sidekick.memes["curiosity"] = 1.0

    world.say(f"{hero.id} was a young superhero who loved {activity.gerund} by {world.setting.place}.")
    world.say(f"{hero.id} also loved curiosity, because every bright scrap on the bank felt like a clue.")
    world.say(f"Beside {hero.id}, {sidekick.id} watched the water and looked for ways to help.")

    world.para()
    world.say(f"One day, {hero.id} and {sidekick.id} went to {world.setting.place} to {activity.verb}.")
    world.say(f"After the rescue, {hero.id}'s {prize.label} was wet and heavy.")
    world.say(f"Then {sidekick.id} noticed {dryer.phrase} in a small boathouse, but it only worked with the right proximity.")

    world.para()
    world.say(f'"If we bring the dryer close, it can help," {sidekick.id} said.')
    world.say(f"{hero.id} frowned at first, because the dryer was too far away and the cape still dripped.")
    world.say(f"But teamwork won the day: {hero.id} held one side, {sidekick.id} held the other, and together they moved the dryer near the cape.")

    _do_activity(world, hero, activity)
    prize.meters["wet"] = 1.0
    dryer.meters["close"] = 1.0
    hero.memes["hope"] = 1.0
    sidekick.memes["hope"] = 1.0

    world.say(f"The warm air hummed, and the wet cape began to transform.")
    prize.meters["wet"] = 0.0
    prize.meters["dry"] = 1.0
    hero.memes["pride"] = 1.0
    sidekick.memes["pride"] = 1.0
    world.say(f"By the end, {hero.id}'s {prize.label} was dry again, and the two heroes stood taller, smiling at the riverbank.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        prize=prize,
        dryer=dryer,
        activity=activity,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short superhero story about {hero.id} at the riverbank where curiosity leads to teamwork and transformation.',
        f"Tell a child-friendly story that uses the words 'proximity' and 'dryer' and ends with a cape becoming dry.",
        f"Write a riverbank rescue story where two heroes solve a wet-problem by working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, prize, activity = f["hero"], f["sidekick"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do by the riverbank?",
            answer=f"{hero.id} was trying to {activity.verb}.",
        ),
        QAItem(
            question=f"What problem did {hero.id}'s {prize.label} have after the rescue?",
            answer=f"The {prize.label} was wet and heavy, so it needed help before {hero.id} could use it again.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sidekick.id} fix the problem?",
            answer="They used teamwork to move the dryer close enough to the wet cape, and the warm air dried it.",
        ),
        QAItem(
            question="Why did the word proximity matter in the story?",
            answer="Proximity mattered because the dryer only helped once the heroes moved it close to the cape.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do something they could not do as well alone.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a big change, like wet gear becoming dry again or a worried feeling turning into pride.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is proximity?",
            answer="Proximity means being close to something.",
        ),
        QAItem(
            question="What is a dryer for?",
            answer="A dryer is a machine that uses warm air to help wet things become dry.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
        for c in g.covers:
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protected(A, P) :- prize_at_risk(A, P), mess_of(A, M), gear(G), guards(G, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), protected(A, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos()")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(hero_name="Mina", hero_gender="girl", sidekick_name="Pip", parent_name="Coach", activity="rescue", prize="cape"),
    StoryParams(hero_name="Leo", hero_gender="boy", sidekick_name="Nova", parent_name="Aunt", activity="splash", prize="boots"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("That combination would not create a real problem-and-fix story.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid story matches those options.")
    _, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(["Pip", "Nova", "Dash", "Bee"])
    parent = args.parent or rng.choice(["Coach", "Aunt", "Uncle"])
    return StoryParams(name, gender, sidekick, parent, activity, prize)


GIRL_NAMES = ["Mina", "Ivy", "Nora", "Zia", "Luna"]
BOY_NAMES = ["Ezra", "Finn", "Kai", "Leo", "Owen"]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
