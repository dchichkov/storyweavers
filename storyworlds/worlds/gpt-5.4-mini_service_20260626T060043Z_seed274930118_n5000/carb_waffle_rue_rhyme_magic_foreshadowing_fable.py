#!/usr/bin/env python3
"""
A small fable-like storyworld about a kitchen helper, a tempting waffle, and a
wise choice about sweets and strength.

Seed words: carb, waffle, rue
Features: Rhyme, Magic, Foreshadowing
Style: Fable
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
# World model
# ---------------------------------------------------------------------------

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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class MagicItem:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str
    sparkle: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"waffle"}),
    "market": Setting(place="the market", indoor=False, affords={"waffle"}),
    "garden": Setting(place="the garden", indoor=False, affords={"waffle"}),
}

ACTIVITIES = {
    "waffle": Activity(
        id="waffle",
        verb="eat the waffle",
        gerund="eating waffles",
        rush="reach for the waffle",
        mess="sticky",
        soil="sticky and crumbly",
        keyword="waffle",
        tags={"waffle", "carb", "sweet"},
    ),
}

PRIZES = {
    "waffle": Prize(
        label="waffle",
        phrase="a warm golden waffle",
        type="waffle",
        region="hands",
        plural=False,
    ),
    "carb-bundle": Prize(
        label="carb bundle",
        phrase="a little carb bundle",
        type="bundle",
        region="hands",
        plural=False,
    ),
}

MAGIC = [
    MagicItem(
        id="sparkle-cloth",
        label="a sparkle cloth",
        guards={"sticky"},
        prep="wrap the waffle in a sparkle cloth first",
        tail="carried the waffle on a sparkle cloth",
        sparkle="The cloth shimmered softly like morning dew.",
    ),
    MagicItem(
        id="sun-plate",
        label="a sun plate",
        guards={"sticky"},
        prep="place it on a sun plate",
        tail="set the treat on a sun plate",
        sparkle="The plate glowed warm and bright, but never burned.",
    ),
]

NAMES = ["Milo", "Penny", "Ada", "Bram", "Luna", "Nia"]
TRAITS = ["kind", "careful", "curious", "gentle", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.id == "waffle" and prize.label in {"waffle", "carb bundle"}


def select_magic(activity: Activity, prize: Prize) -> Optional[MagicItem]:
    if not prize_at_risk(activity, prize):
        return None
    return MAGIC[0] if prize.label == "waffle" else MAGIC[1]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not reasonably trouble that prize. "
        f"Try the waffle itself or a small carb bundle.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('traits', []) if t != 'little'), 'kind')} "
        f"{hero.type} who loved the kitchen's early light."
    )


def setup_story(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} liked {activity.gerund}, and {hero.pronoun('possessive')} {parent.label} knew "
        f"that a waffle could be a small, sweet trouble."
    )
    world.say(
        f"One bright morning, {parent.label} brought {hero.pronoun('object')} {prize.phrase}, "
        f"and {hero.id} smiled at the warm smell of honey."
    )


def foreshadow(world: World, prize: Entity, activity: Activity) -> None:
    world.say(
        f"A tiny crumb fell to the table, and the old cat blinked twice as if to say, "
        f"'{activity.keyword} can stick fast.'"
    )
    world.say(
        f"{prize.label.capitalize()}s are happy things, but happy things can make a mess when they are rushed."
    )


def warn(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"'{activity.verb} too quickly may leave you rueful,' {parent.label} said. "
        f"'You may rue a sticky shirt and a sad plate.'"
    )


def magic_offer(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> MagicItem:
    item = select_magic(activity, prize)
    if item is None:
        raise StoryError(explain_rejection(activity, prize))
    world.say(
        f"{parent.label} smiled and held up {item.label}. {item.sparkle} "
        f"'How about we {item.prep} and then {activity.verb} with care?'"
    )
    return item


def accept(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity, item: MagicItem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["rue"] = 0.0
    world.say(
        f"{hero.id} nodded, because wise hearts know that magic is not for showing off, "
        f"but for doing things well."
    )
    world.say(
        f"So they {item.tail}, and {hero.id} ate slowly, {activity.gerund} with tidy hands; "
        f"{prize.label} stayed clean, and there was nothing to rue."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"traits": ["little", trait]}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    setup_story(world, hero, parent, prize, activity)
    world.para()
    foreshadow(world, prize, activity)
    warn(world, parent, hero, prize, activity)
    item = magic_offer(world, parent, hero, prize, activity)
    world.para()
    accept(world, hero, parent, prize, activity, item)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": activity,
        "setting": setting,
        "magic": item,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short fable for children about "{activity.keyword}", a warm waffle, and a wise compromise.',
        f"Tell a gentle story where {hero.id} wants to {activity.verb} but {parent.label} worries about a sticky mess.",
        f"Write a rhyming, magical fable that includes a waffle and ends with a clean, happy table.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, prize, magic = f["hero"], f["parent"], f["activity"], f["prize"], f["magic"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the waffle?",
            answer=f"{hero.id} wanted to {activity.verb}, but the grown-up saw that rushing could make a sticky mess.",
        ),
        QAItem(
            question=f"Why did {parent.label} mention rue?",
            answer=(
                f"{parent.label} used the word rue to warn that {hero.id} might be sorry later if {prize.label} got sticky. "
                f"It was a gentle reminder to slow down and choose wisely."
            ),
        ),
        QAItem(
            question=f"How did the magic item help the story end well?",
            answer=(
                f"{magic.label} kept the waffle tidy while {hero.id} ate carefully, so the food stayed lovely and "
                f"the table did not become a mess."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a waffle?",
            answer="A waffle is a cooked breakfast food with a bumpy grid pattern that can hold syrup or fruit.",
        ),
        QAItem(
            question="What does carb mean?",
            answer="A carb is a kind of food that gives the body energy, like bread, rice, pasta, or waffles.",
        ),
        QAItem(
            question="What does it mean to rue something?",
            answer="To rue something means to feel sorry about it later.",
        ),
        QAItem(
            question="Why can magic be useful in a fable?",
            answer="In a fable, magic can help show a lesson by making a problem easier to solve in a special way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk when the story activity and prize match the same food.
at_risk(A,P) :- activity(A), prize(P), matches(A,P).

% Magic is reasonable when it guards the sticky outcome.
good_magic(M,A,P) :- at_risk(A,P), magic(M), guards(M, sticky).

valid_story(Place,A,P) :- afford(Place,A), at_risk(A,P), good_magic(_,A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("matches", aid, "waffle"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.label == "waffle":
            lines.append(asp.fact("matches", "waffle", pid))
        if p.label == "carb bundle":
            lines.append(asp.fact("matches", "waffle", pid))
    for m in MAGIC:
        lines.append(asp.fact("magic", m.id))
        for g in sorted(m.guards):
            lines.append(asp.fact("guards", m.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted(valid_combos())
    asp_set = asp_valid_stories()
    py_as_tuples = [(p, a, pr) for (p, a, pr) in py]
    if sorted(py_as_tuples) == sorted(asp_set):
        print(f"OK: ASP matches Python reasonableness gate ({len(py_as_tuples)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py_as_tuples))
    print("asp:", sorted(asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[act], prize) and select_magic(ACTIVITIES[act], prize):
                    combos.append((place, act, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about waffle, carb, and rue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.memes, e.meters)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=r, name="Milo", gender="boy", parent="mother", trait="kind"))
                   for (p, a, r) in valid_combos()]
    else:
        samples = []
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
