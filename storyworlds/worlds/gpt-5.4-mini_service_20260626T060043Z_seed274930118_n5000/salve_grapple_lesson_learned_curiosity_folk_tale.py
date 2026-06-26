#!/usr/bin/env python3
"""
storyworlds/worlds/salve_grapple_lesson_learned_curiosity_folk_tale.py
======================================================================

A small folk-tale story world about curiosity, a risky grapple, and a healing
salve that helps the hero learn a gentle lesson.

Seed tale:
---
A curious little field mouse named Miri kept peeking at the bright blue berries
that grew high in the briar hedge. Her granny warned her not to grab them with
bare paws, because the briars could scratch. But Miri was too curious. She
grappled with the vines, got stung by thorns, and came home with sore paws.

Granny washed the scratches, spread on a green salve, and told Miri that
curiosity is a fine lantern, but it should walk beside patience. The next day,
Miri used a stick and a basket, and the berries came home safely.

World ingredients:
- physical meters: soreness, scratch, mess, care, freshness
- emotional memes: curiosity, worry, patience, relief, pride, lesson_learned

This script builds a tiny simulated domain with a clear beginning, turn, and
ending image, plus a matching ASP twin.
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


# ---------------------------------------------------------------------------
# Entity and world model
# ---------------------------------------------------------------------------
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    scent: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Salve:
    id: str
    label: str
    smell: str
    cure: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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


THRESHOLD = 1.0


def bump(ent: Entity, meter: str, amount: float = 1.0) -> None:
    ent.meters[meter] = ent.meters.get(meter, 0.0) + amount


def bump_meme(ent: Entity, meme: str, amount: float = 1.0) -> None:
    ent.memes[meme] = ent.memes.get(meme, 0.0) + amount


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "briar_hollow": Setting(place="the briar hollow", scent="green and sweet", affords={"grapple"}),
    "river_path": Setting(place="the river path", scent="wet reeds", affords={"grapple"}),
    "cottage_garden": Setting(place="the cottage garden", scent="mint and earth", affords={"grapple"}),
}

ACTIVITIES = {
    "grapple": Activity(
        id="grapple",
        verb="grapple for the berries",
        gerund="grappling for the berries",
        rush="reach into the briars",
        risk="thorn scratches",
        mess="scratch",
        zone={"paws", "arms"},
        keyword="berries",
        tags={"curiosity", "lesson_learned"},
    )
}

PRIZES = {
    "berries": Prize(id="berries", label="berries", phrase="bright blue berries", region="arms", plural=True),
    "honeycomb": Prize(id="honeycomb", label="honeycomb", phrase="a sweet honeycomb", region="arms"),
    "red_apple": Prize(id="red_apple", label="apple", phrase="a red apple", region="arms"),
}

SALVES = {
    "green_salve": Salve(
        id="green_salve",
        label="green salve",
        smell="fresh mint",
        cure="soothe the stings",
        prep="wash the scratches and spread on the green salve",
        tail="sat by the hearth until the sting grew small",
    ),
    "flower_salve": Salve(
        id="flower_salve",
        label="flower salve",
        smell="sweet flowers",
        cure="cool the scratches",
        prep="clean the scratches and dab on the flower salve",
        tail="rested under a quilt until the soreness softened",
    ),
}

HERO_NAMES = ["Miri", "Tessa", "Pip", "Nell", "Rowan", "Lark"]
ELDER_NAMES = ["Granny", "Nana", "Old Bramble", "Grandma Reed"]

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    salve: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk if the activity reaches the region where it is held.
at_risk(A, P) :- reaches(A, R), held_on(P, R).

% A salve is compatible when it can soothe the specific risk caused by the activity.
good_fix(S, A, P) :- at_risk(A, P), risk_kind(A, K), cures(S, K).

valid_story(Place, A, P, S, Gender) :- affords(Place, A), at_risk(A, P), good_fix(S, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_kind", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("reaches", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("held_on", pid, prize.region))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
        if prize.plural:
            lines.append(asp.fact("plural", pid))
    for sid, salve in SALVES.items():
        lines.append(asp.fact("salve", sid))
        lines.append(asp.fact("cures", sid, "scratch"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def lesson_line() -> str:
    return "The lesson learned was that curiosity is good, but patience keeps small paws safe."


def setup_line(hero: Entity, elder: Entity, prize: Prize, setting: Setting) -> str:
    return (
        f"{hero.id} was a little {hero.type} who loved wandering near {setting.place}. "
        f"{hero.pronoun().capitalize()} liked {setting.scent} days and dreamed about {prize.phrase}."
    )


def conflict_line(hero: Entity, elder: Entity, activity: Activity, prize: Prize) -> str:
    return (
        f"One day, {hero.id} saw {prize.phrase} tucked high in the briars and wanted to {activity.verb}. "
        f"But {elder.id} warned that the thorns could leave {hero.pronoun('possessive')} paws sore."
    )


def resolution_line(hero: Entity, elder: Entity, salve: Salve, prize: Prize) -> str:
    return (
        f"After that, {elder.id} used {salve.label} to {salve.cure} and said the red sting would fade. "
        f"{hero.id} nodded, and {hero.pronoun().capitalize()} remembered the warning."
    )


def ending_line(hero: Entity, prize: Prize, salve: Salve) -> str:
    return (
        f"The next morning, {hero.id} came back with a careful stick and a small basket, "
        f"so {hero.pronoun('possessive')} paws stayed clean, {prize.label} came home safely, "
        f"and {salve.label} stayed on the shelf like a little green promise."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    salve = SALVES[params.salve]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        meters={"care": 0.0}, memes={"curiosity": 1.0, "worry": 0.0, "patience": 0.0, "relief": 0.0, "lesson_learned": 0.0},
    ))
    elder = world.add(Entity(
        id=params.elder, kind="character", type="grandmother" if params.gender == "girl" else "grandfather",
        label=params.elder,
        meters={"care": 1.0},
        memes={"worry": 1.0, "patience": 1.0},
    ))
    berry = world.add(Entity(
        id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=elder.id, plural=prize.plural,
    ))
    world.facts.update(hero=hero, elder=elder, prize=berry, activity=activity, salve=salve)
    return world


def simulate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    prize: Entity = world.facts["prize"]
    activity: Activity = world.facts["activity"]
    salve: Salve = world.facts["salve"]

    # Act 1
    world.say(setup_line(hero, elder, prize, world.setting))
    bump_meme(hero, "curiosity", 1.0)
    bump_meme(hero, "lesson_learned", 0.0)

    # Act 2
    world.para()
    world.say(conflict_line(hero, elder, activity, prize))
    bump_meme(hero, "curiosity", 1.0)
    bump_meme(elder, "worry", 1.0)
    hero.meters["scratch"] = 0.0
    hero.meters["soreness"] = 0.0
    world.zone = set(activity.zone)
    bump(hero, "scratch", 1.0)
    bump(hero, "soreness", 1.0)
    bump_meme(hero, "worry", 1.0)

    # Act 3
    world.para()
    world.say(
        f"{hero.id} came home with {hero.pronoun('possessive')} paws stinging, and {elder.id} did not scold. "
        f"Instead, {elder.id} said, \"First we {salve.prep}.\""
    )
    bump_meme(hero, "patience", 1.0)
    bump_meme(hero, "relief", 1.0)
    bump_meme(hero, "lesson_learned", 1.0)
    bump(hero, "freshness", 1.0)
    world.say(resolution_line(hero, elder, salve, prize))
    world.para()
    world.say(ending_line(hero, prize, salve))
    world.para()
    world.say(lesson_line())

    world.facts["resolved"] = True
    world.facts["conflict"] = True
    world.facts["ending"] = "careful stick and small basket"


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, prize, salve = f["hero"], f["activity"], f["prize"], f["salve"]
    return [
        f'Write a short folk tale for a small child about "{activity.keyword}" and a lesson learned.',
        f"Tell a gentle story where {hero.id} is full of curiosity, grapples for {prize.label}, and later uses {salve.label}.",
        f'Write a child-friendly folk tale that includes the words "{activity.id}", "{salve.label}", and "lesson learned".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, activity, salve = f["hero"], f["elder"], f["prize"], f["activity"], f["salve"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the berries?",
            answer=f"{hero.id} wanted to {activity.verb} because {hero.pronoun().capitalize()} was curious about the {prize.label}.",
        ),
        QAItem(
            question=f"Why did {elder.id} worry about the choice?",
            answer=f"{elder.id} worried because the briars could leave {hero.pronoun('possessive')} paws sore and scratchy.",
        ),
        QAItem(
            question=f"What did {elder.id} use to help after the grapple?",
            answer=f"{elder.id} used {salve.label} to {salve.cure}, so the stings could calm down.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that curiosity is good, but patience and a careful tool keep you safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    salve = f["salve"]
    return [
        QAItem(
            question="What is a salve?",
            answer="A salve is a soft ointment or cream that people spread on sore skin to help it feel better.",
        ),
        QAItem(
            question="Why are briars hard to grab?",
            answer="Briars are hard to grab because their thorns can scratch skin and make it sting.",
        ),
        QAItem(
            question="Why is curiosity useful?",
            answer="Curiosity is useful because it helps someone notice new things, ask questions, and learn.",
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    for salve_id in SALVES:
                        combos.append((place, act_id, prize_id, salve_id, "girl"))
                        combos.append((place, act_id, prize_id, salve_id, "boy"))
    return combos


def asp_valid_combos_py() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("briar_hollow", "grapple", "berries", "green_salve", "Miri", "girl", "Granny"),
    StoryParams("river_path", "grapple", "honeycomb", "flower_salve", "Pip", "boy", "Grandma Reed"),
    StoryParams("cottage_garden", "grapple", "red_apple", "green_salve", "Nell", "girl", "Old Bramble"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale world about curiosity, grapple, and salve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--salve", choices=SALVES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.salve is None or c[3] == args.salve)
              and (args.gender is None or c[4] == args.gender)]
    if not combos:
        raise StoryError("No valid folk-tale combination matches the given options.")
    place, activity, prize, salve, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, salve=salve, name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/5."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos_py()
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize}, salve: {p.salve})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
