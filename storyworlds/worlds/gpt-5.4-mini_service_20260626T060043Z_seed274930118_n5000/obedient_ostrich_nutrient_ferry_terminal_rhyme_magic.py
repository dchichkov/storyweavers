#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/obedient_ostrich_nutrient_ferry_terminal_rhyme_magic.py
===============================================================================================================

A small, standalone story world about an obedient ostrich, a nutrient delivery,
and a ferry terminal where rhyme and magic help turn trouble into a safe trip.

Seed tale used to shape the simulation:
---
At a ferry terminal, an obedient ostrich named Olive was helping carry a crate
of nutrient powder to a garden island. The wind kept tugging at the crate and
making the labels flap. Olive wanted to help, but the path to the ferry was
slippery and the tide was rising. A dockkeeper taught Olive a little rhyme,
and when Olive repeated it, the crate began to glow with magic and float just
high enough to stay dry. Olive followed the instructions carefully, boarded the
ferry, and delivered the nutrients in time for the island garden to grow.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "safe": 0.0, "magic": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "obedience": 0.0, "awe": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"ostrich", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the ferry terminal"
    affords: set[str] = field(default_factory=lambda: {"load", "board", "cross", "rhyme"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "ostrich"
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    rhyme: str
    tail: str


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.weather = self.weather
        c.facts = dict(self.facts)
        return c


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot support {activity.id}.")
    actor.memes["obedience"] += 1
    actor.memes["worry"] += 1
    world.facts["activity"] = activity
    if narrate:
        world.say(f"{actor.id} {activity.verb} at {world.setting.place}.")
    if activity.id == "load":
        actor.meters["safe"] += 0.2
    if activity.id == "cross":
        actor.meters["safe"] += 0.5


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    wet = prize.meters["wet"] >= THRESHOLD
    return {"wet": wet, "safe": prize.meters["safe"], "magic": prize.meters["magic"]}


def rhyme_magic(world: World, hero: Entity, charm: Charm, prize: Entity) -> bool:
    world.say(
        f'A dockkeeper hummed, "{charm.rhyme}" '
        f"{charm.tail}"
    )
    hero.memes["awe"] += 1
    hero.meters["safe"] += 1
    prize.meters["magic"] += 1
    prize.meters["safe"] += 1
    return True


def setup_story(world: World, hero: Entity, guide: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was an obedient {hero.type} at {world.setting.place}, "
        f"carrying {prize.phrase} for a garden island."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {activity.verb}, because "
        f"{activity.gerund} was part of the day's adventure."
    )
    world.say(
        f"{guide.id} watched the sky and warned that the wind and spray could spoil {prize.it()}."
    )


def conflict_story(world: World, hero: Entity, guide: Entity, prize: Entity, activity: Activity) -> None:
    pred = predict(world, hero, activity, prize.id)
    hero.memes["worry"] += 1
    if pred["wet"]:
        world.say(
            f"The path to the ferry was slick, and the crate could get {activity.risk}."
        )
    world.say(
        f'{guide.id} pointed to a little rhyme and said, "Repeat this before the ferry leaves."'
    )


def resolution_story(world: World, hero: Entity, guide: Entity, prize: Entity, charm: Charm) -> None:
    rhyme_magic(world, hero, charm, prize)
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} obeyed at once, and the crate lifted in a tiny glow of magic."
    )
    world.say(
        f"{hero.id} boarded the ferry with {prize.it()}, and the spray slid under it without touching the lid."
    )
    world.say(
        f"By the time the ferry reached the island, the nutrient crate was dry, safe, and ready for the garden."
    )


SETTINGS = {
    "ferry_terminal": Setting(),
}

ACTIVITIES = {
    "load": Activity(
        id="load",
        verb="load the nutrient crate onto the ferry",
        gerund="loading the nutrient crate",
        rush="hurry the crate toward the dock",
        risk="wet and spoiled",
        weather="windy",
        keyword="nutrient",
        tags={"nutrient", "ferry", "harbor"},
    ),
    "cross": Activity(
        id="cross",
        verb="cross the harbor by ferry",
        gerund="riding the ferry",
        rush="dash across the ramp",
        risk="sprayed",
        weather="windy",
        keyword="ferry",
        tags={"ferry", "harbor"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="speak a magic rhyme",
        gerund="saying the rhyme",
        rush="blurt out the words",
        risk="scattered",
        weather="calm",
        keyword="rhyme",
        tags={"rhyme", "magic"},
    ),
}

PRIZES = {
    "nutrient_crate": Prize(
        label="nutrient crate",
        phrase="a sealed crate of nutrient powder",
        type="crate",
    ),
    "nutrient_sack": Prize(
        label="nutrient sack",
        phrase="a packed sack of nutrients",
        type="sack",
    ),
}

CHARMS = {
    "rhyme_glow": Charm(
        id="rhyme_glow",
        label="a rhyme charm",
        effect="magic glow",
        rhyme="One, two, three, and four, keep the nutrient safe for shore!",
        tail="The words hummed like a song, and the crate floated just above the wet boards.",
    )
}

HEROES = ["Olive", "Otto", "Opal", "Orin", "Oona"]
GUIDES = ["Dockkeeper", "Ferry Captain", "Harbor Helper"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    guide: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An obedient ostrich at a ferry terminal, with rhyme and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(combos)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(HEROES),
        guide=args.guide or rng.choice(GUIDES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world.weather = ACTIVITIES[params.activity].weather

    hero = world.add(Entity(id=params.name, kind="character", type="ostrich", traits=["obedient", "brave"]))
    guide = world.add(Entity(id=params.guide, kind="character", type="person", traits=["helpful"]))
    prize = world.add(Entity(
        id=params.prize,
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=guide.id,
    ))

    activity = ACTIVITIES[params.activity]
    charm = CHARMS["rhyme_glow"]

    setup_story(world, hero, guide, prize, activity)
    world.para()
    conflict_story(world, hero, guide, prize, activity)
    world.para()
    resolution_story(world, hero, guide, prize, charm)

    world.facts.update(hero=hero, guide=guide, prize=prize, activity=activity, charm=charm, resolved=True)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        "Write a short adventure for young children about an obedient ostrich, a ferry terminal, and a little magic rhyme.",
        f"Tell a story where {hero.id} wants to {activity.verb} but must protect {prize.phrase}.",
        "Write a gentle adventure that includes rhyme, magic, and a safe crossing by ferry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    prize = f["prize"]
    activity = f["activity"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"Who is the story about at the ferry terminal?",
            answer=f"The story is about {hero.id}, an obedient ostrich who helps carry {prize.phrase}.",
        ),
        QAItem(
            question=f"What worried {guide.id} about the crate?",
            answer=f"{guide.id} worried that the wind and spray could make {prize.label} wet and spoiled.",
        ),
        QAItem(
            question="What did the dockkeeper use to help?",
            answer=f"The dockkeeper used a magic rhyme: {charm.rhyme}",
        ),
        QAItem(
            question=f"What did {hero.id} do after hearing the rhyme?",
            answer=f"{hero.id} obeyed, let the magic glow lift the crate, and boarded the ferry safely.",
        ),
        QAItem(
            question=f"Why was the nutrient crate important?",
            answer="The nutrient crate mattered because it was meant for the garden island and had to arrive dry and ready to use.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ferry terminal?",
            answer="A ferry terminal is a place by the water where people and cargo wait to board a ferry.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a phrase or poem with words that sound similar at the ends, and it can be fun to say aloud.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful in a story that can make unusual things happen, like a crate floating safely.",
        ),
        QAItem(
            question="What is a nutrient?",
            answer="A nutrient is something living things need to grow and stay healthy, like food for a plant or animal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Act,Prize) :- place(Place), activity(Act), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


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
    StoryParams(place="ferry_terminal", activity="load", prize="nutrient_crate", name="Olive", guide="Dockkeeper"),
    StoryParams(place="ferry_terminal", activity="cross", prize="nutrient_sack", name="Otto", guide="Ferry Captain"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
