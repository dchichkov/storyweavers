#!/usr/bin/env python3
"""
storyworlds/worlds/subsidiary_galore_suspense_tall_tale.py
===========================================================

A small tall-tale storyworld about a bustling fairground with a main booth and
a subsidiary booth, plenty of treats galore, and a suspenseful missing item
that turns into a harmless surprise.

Premise:
- A child and a grown-up run a traveling fair booth.
- The booth sells snacks galore.
- A prized item goes missing from the subsidiary booth.

Tension:
- The child wants to perform a flashy trick, but the grown-up notices the
  missing item first.
- Suspense grows while they search the booth, cart, and shelves.

Turn:
- They discover the missing prize tucked into the subsidiary booth by a helper
  animal or a windy happenstance.

Resolution:
- The child completes the trick, the crowd cheers galore, and the booth
  settles down happily.

The story style aims for tall-tale exaggeration, child-friendly suspense, and a
clear state-driven resolution image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the fairground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    suspense: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    hidden_in: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    effect: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def _default_meters() -> dict[str, float]:
    return {"busy": 0.0}


def _default_memes() -> dict[str, float]:
    return {"joy": 0.0, "worry": 0.0, "suspense": 0.0, "relief": 0.0}


def make_entity(**kwargs) -> Entity:
    ent = Entity(**kwargs)
    if not ent.meters:
        ent.meters = _default_meters()
    if not ent.memes:
        ent.memes = _default_memes()
    return ent


def build_story(world: World, hero: Entity, grownup: Entity, prize: Entity, activity: Activity, gear: Optional[Gear]) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big heart and a laugh that could "
        f"bounce off the tents like a rubber ball."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} loved the fairground because it had snacks galore, "
        f"bright flags, and a tiny subsidiary booth tucked beside the main one."
    )
    world.say(
        f"That day, {hero.id} and {grownup.label} were helping at {world.setting.place}, "
        f"and {hero.id} was ready to {activity.verb}."
    )
    world.say(
        f"{prize.phrase.capitalize()} was meant for the subsidiary booth, and everybody expected it to stay put."
    )

    world.para()
    hero.memes["suspense"] += 1
    grownup.memes["worry"] += 1
    world.say(
        f"Then the air grew hush-quiet. The crowd stopped chewing, the flags stopped flapping, "
        f"and somebody noticed {prize.label} was gone."
    )
    world.say(
        f"{grownup.label} peered under the counter, behind the crates, and around the side wheels. "
        f"{hero.id} peeked too, feeling the suspense creep up like a cat on a fence."
    )
    world.say(
        f'"If we do not find it soon," {grownup.label} said, "the whole booth will be in a pickle."'
    )

    world.para()
    if gear:
        hero.memes["joy"] += 1
        world.say(
            f"At last, {hero.id} spotted a clue and grabbed {gear.label}. "
            f"{gear.prep.capitalize()}, and the search made a clever little plan instead of a panic."
        )
        world.say(
            f"They followed the clue to the subsidiary booth, where the missing {prize.label} had been tucked away all snug and tidy."
        )
        world.say(
            f"Nobody was in trouble at all; the wind and the bustle had simply nudged {prize.label} out of sight."
        )
        world.say(
            f"{hero.id} let out a mighty grin, {grownup.label} laughed with relief, and the fairground felt friendly again."
        )
        world.say(
            f"Then {hero.id} {activity.gerund}, and the crowd cheered galore as the booth shone like a lantern in the dusk."
        )
    else:
        world.say(
            f"At last, {hero.id} found the missing {prize.label} without any special tool at all."
        )
        world.say(
            f"It had rolled behind the subsidiary booth, where a crate had hidden it like a squirrel with a shiny acorn."
        )
        world.say(
            f"{grownup.label} clapped, the suspense melted away, and {hero.id} got to {activity.verb} after all."
        )
        world.say(
            f"The crowd cheered galore, and the fairground felt bright as a box of fireflies."
        )

    world.facts.update(hero=hero, grownup=grownup, prize=prize, activity=activity, gear=gear)


SETTINGS = {
    "fairground": Setting(place="the fairground", affords={"juggle", "sing", "parade"}),
    "big_top": Setting(place="the big top", affords={"juggle", "sing"}),
    "boardwalk": Setting(place="the boardwalk", affords={"parade", "sing"}),
}

ACTIVITIES = {
    "juggle": Activity(
        id="juggle",
        verb="juggle three shiny apples",
        gerund="juggling three shiny apples",
        rush="dash toward the ring",
        suspense="the apples might tumble",
        keyword="galore",
        tags={"galore", "suspense"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing a booming fairground song",
        gerund="singing a booming fairground song",
        rush="step onto the crate",
        suspense="the crowd might go quiet",
        keyword="suspense",
        tags={"suspense"},
    ),
    "parade": Activity(
        id="parade",
        verb="lead the parade with a giant wink",
        gerund="leading the parade with a giant wink",
        rush="march down the lane",
        suspense="the banner might vanish",
        keyword="galore",
        tags={"galore", "suspense"},
    ),
}

PRIZES = {
    "banner": Prize(
        label="banner",
        phrase="a striped banner with gold stars",
        type="banner",
        hidden_in="the subsidiary booth",
    ),
    "pie": Prize(
        label="pie",
        phrase="a blueberry pie galore",
        type="pie",
        hidden_in="under the side table",
    ),
    "horn": Prize(
        label="horn",
        phrase="a shiny brass horn",
        type="horn",
        hidden_in="behind the candy crate",
    ),
}

GEAR = {
    "lantern": Gear(
        id="lantern",
        label="a little lantern",
        effect="shines on hidden corners",
        prep="The lantern shone under the counter",
        tail="Its glow made the missing prize easy to spot",
    ),
    "rope": Gear(
        id="rope",
        label="a soft rope",
        effect="keeps things from rolling away",
        prep="The rope made a tidy search line",
        tail="So nothing could slip out of sight again",
    ),
}

NAMES = ["Mabel", "Clem", "Nina", "Pip", "Jasper", "Ruby", "Otis", "June"]
GROWNUPS = ["the ringmaster", "the fair boss", "the auntie", "the uncle"]
TYPES = ["girl", "boy"]
TRAITS = ["brave", "cheery", "curious", "spirited"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale suspense at a fairground with a subsidiary booth and snacks galore.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=GROWNUPS)
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
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    grownup = args.grownup or rng.choice(GROWNUPS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, grownup=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(make_entity(id=params.name, kind="character", type=params.gender))
    grownup = world.add(make_entity(id="grownup", kind="character", type="adult", label=params.grownup))
    prize = world.add(make_entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=grownup.id,
    ))
    activity = ACTIVITIES[params.activity]
    gear = GEAR["lantern"] if activity.id in {"juggle", "parade"} else GEAR["rope"]

    build_story(world, hero, grownup, prize, activity, gear)

    prompts = [
        f'Write a short tall-tale story about a child, a subsidiary booth, and {params.prize} galore.',
        f'Tell a suspenseful fairground story where {params.name} must {activity.verb} after a missing prize is found.',
        f'Write a child-friendly story using the words "subsidiary", "galore", and "suspense".',
    ]
    story_qa = [
        QAItem(
            question=f"What was missing from the subsidiary booth?",
            answer=f"{prize.phrase.capitalize()} was missing at first, which made everybody feel suspense.",
        ),
        QAItem(
            question=f"Why did {params.grownup} get worried?",
            answer=f"{params.grownup.capitalize()} got worried because the prize was gone and the booth could not finish its job until it was found.",
        ),
        QAItem(
            question=f"What did {params.name} do at the end?",
            answer=f"{params.name} {activity.gerund}, and the crowd cheered galore when the story ended happily.",
        ),
    ]
    world_qa = [
        QAItem(question="What does galore mean?", answer="Galore means there is a whole lot of something."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of wondering what will happen next."),
        QAItem(question="What does subsidiary mean?", answer="Subsidiary means something that is smaller or attached to a main one, like a side booth next to a bigger booth."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place,Act,Prize) :- setting(Place), affords(Place,Act), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, act, prize in valid_combos():
            params = StoryParams(place=place, activity=act, prize=prize, name="Mabel", gender="girl", grownup="the ringmaster", trait="curious", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
