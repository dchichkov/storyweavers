#!/usr/bin/env python3
"""
A small folk-tale storyworld about a disc, a mob, sharing, and humor.

Premise:
A humble disc is valued by a small crowd. The crowd's mood can turn from
grabby to generous when someone uses wit, kindness, or a clever trade.
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

# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Disc:
    label: str
    phrase: str
    type: str = "disc"
    value: str = "bright"
    shareable: bool = True


@dataclass
class TaleAct:
    id: str
    want: str
    bustle: str
    twist: str
    humor: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "green": Setting(place="the green", vibe="bright", affords={"share", "humor"}),
    "market": Setting(place="the market square", vibe="busy", affords={"share", "humor"}),
    "oak": Setting(place="the old oak tree", vibe="merry", affords={"share", "humor"}),
    "brook": Setting(place="the brookside", vibe="soft", affords={"share", "humor"}),
}

ACTIVITIES = {
    "share_disc": TaleAct(
        id="share_disc",
        want="share the disc",
        bustle="hold the disc up high",
        twist="everyone wanted the first turn",
        humor="one fellow kept calling it a flying pancake",
        outcome="the crowd learned to take turns",
        tags={"disc", "share", "humor"},
    ),
    "clean_disc": TaleAct(
        id="clean_disc",
        want="polish the disc",
        bustle="rub the disc with a leaf",
        twist="the mud made it look like a moon in a puddle",
        humor="a child laughed that it was a soup plate for stars",
        outcome="the disc shone again",
        tags={"disc", "humor"},
    ),
    "spin_disc": TaleAct(
        id="spin_disc",
        want="spin the disc",
        bustle="tap the disc with a stick",
        twist="the disc went whirling into the grass",
        humor="the mob chased it in circles like hens after a beetle",
        outcome="the laughter made the waiting easy",
        tags={"disc", "mob", "humor"},
    ),
}

TRAITS = ["kind", "cheerful", "quick-witted", "patient", "merry", "lively"]
GIRL_NAMES = ["Mina", "Lena", "Pia", "Sera", "Nora", "Tia"]
BOY_NAMES = ["Jem", "Oren", "Pavel", "Tobin", "Nico", "Bram"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(Place).
% affords(Place,Act).
% activity(Act).
% tag(Act,Tag).
% gender(G).
% companion(C).

% A story is valid if the setting affords the activity and the act uses
% either disc, share, or humor as its theme.
theme_ok(A) :- tag(A, disc).
theme_ok(A) :- tag(A, share).
theme_ok(A) :- tag(A, humor).

valid(Place, Act, Gender, Companion) :-
    setting(Place),
    affords(Place, Act),
    theme_ok(Act),
    gender(Gender),
    companion(Companion).
#show valid/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act_id, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", act_id))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", act_id, tag))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    for c in ("fox", "crow", "goat", "mouse"):
        lines.append(asp.fact("companion", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            if "disc" not in act.tags:
                continue
            for gender in ("girl", "boy"):
                for companion in ("fox", "crow", "goat", "mouse"):
                    combos.append((place, act_id, gender, companion))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    world = World(setting=setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"joy": 0.0},
        memes={"desire": 0.0, "humor": 0.0, "sharing": 0.0, "pique": 0.0, "warmth": 0.0},
    ))
    mob = world.add(Entity(
        id="mob",
        kind="character",
        type="crowd",
        label=f"the {params.companion}-led mob",
        plural=True,
        meters={"restlessness": 0.0},
        memes={"greed": 0.0, "laughing": 0.0, "sharing": 0.0},
    ))
    disc = world.add(Entity(
        id="disc",
        kind="thing",
        type="disc",
        label="disc",
        phrase="a bright little disc",
        owner=hero.id,
        meters={"shine": 1.0, "dust": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.companion,
        label=params.companion,
        meters={"help": 0.0},
        memes={"wit": 1.0},
    ))
    world.facts.update(hero=hero, mob=mob, disc=disc, helper=helper, act=act, params=params)
    return world


def do_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mob: Entity = f["mob"]
    disc: Entity = f["disc"]
    act: TaleAct = f["act"]
    helper: Entity = f["helper"]

    world.say(
        f"Once, by {world.setting.place}, there lived {hero.pronoun('possessive')} "
        f"little {disc.label}, bright as a coin and light as a promise."
    )
    world.say(
        f"{hero.id} loved to {act.want}, and {helper.label} the {helper.type} came "
        f"trotting by with a grin."
    )
    mob.memes["greed"] += 1
    hero.memes["desire"] += 1
    world.para()
    world.say(
        f"Then the {world.setting.vibe} day drew a small mob near, and every one of them "
        f"wanted a hand on the disc."
    )


def do_conflict(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mob: Entity = f["mob"]
    disc: Entity = f["disc"]
    act: TaleAct = f["act"]
    helper: Entity = f["helper"]

    mob.meters["restlessness"] += 1
    hero.memes["pique"] += 1
    world.say(
        f"The crowd reached in at once, but {hero.id} held the disc close and said, "
        f"\"One at a time!\""
    )
    world.say(
        f"That did not help much, for the mob was noisy, and even the {helper.type} "
        f"laughed that {act.humor}."
    )
    world.say(
        f"To stop the tugging, {helper.label} tapped the disc and made it spin like a "
        f"small sun on a string."
    )
    disc.meters["shine"] += 0.5
    hero.memes["humor"] += 1
    mob.memes["laughing"] += 1


def do_resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mob: Entity = f["mob"]
    disc: Entity = f["disc"]
    act: TaleAct = f["act"]
    helper: Entity = f["helper"]

    mob.memes["sharing"] += 1
    hero.memes["sharing"] += 1
    hero.meters["joy"] += 1
    world.para()
    world.say(
        f"Then {helper.label} told a joke so plain and merry that even the grumpiest face "
        f"had to soften."
    )
    world.say(
        f"{hero.id} smiled and named a fair turn for each one, and the mob, hearing the "
        f"kind plan, passed the disc around."
    )
    world.say(
        f"By dusk, {act.outcome}, and the bright disc kept moving from palm to palm while "
        f"everyone laughed under {world.setting.place}."
    )


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    do_setup(world)
    do_conflict(world)
    do_resolution(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    act: TaleAct = f["act"]
    return [
        f"Write a folk-tale story about a {params.gender} who tries to {act.want} with a mob, using humor to solve the problem.",
        f"Tell a short children's tale where a bright disc causes a crowd to quarrel, and a funny idea leads to sharing.",
        f"Write a gentle story set at {world.setting.place} about a disc, a mob, and a fair way to take turns.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mob: Entity = f["mob"]
    disc: Entity = f["disc"]
    act: TaleAct = f["act"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What was the little thing everyone wanted at {world.setting.place}?",
            answer=f"It was {disc.phrase}. The disc was bright, so the mob wanted a turn with it.",
        ),
        QAItem(
            question=f"Why did the mob start crowding around {hero.id}?",
            answer=f"The mob wanted the disc too, because it looked bright and fun to share.",
        ),
        QAItem(
            question=f"How did {helper.label} help solve the trouble?",
            answer=f"{helper.label} used humor and a clever joke, then helped make a fair sharing plan.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the mob was sharing instead of tugging, and the disc passed from hand to hand without a quarrel.",
        ),
        QAItem(
            question=f"What kind of tale was this about the disc and the crowd?",
            answer=f"It was a folk tale with a small crowd, a funny turn, and a kind answer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people have a turn with something instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the funny part of a story or joke that makes people smile or laugh.",
        ),
        QAItem(
            question="What is a disc?",
            answer="A disc is a flat round object, like a little plate or a toy that can be passed around.",
        ),
        QAItem(
            question="What is a mob?",
            answer="A mob is a crowd of people all gathered closely together, often acting as one noisy group.",
        ),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: disc, mob, sharing, humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["fox", "crow", "goat", "mouse"])
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.gender is None or c[2] == args.gender)
        and (args.companion is None or c[3] == args.companion)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, gender, companion = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
    return StorySample(
        params=params,
        story=world.story if hasattr(world, "story") else world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="green", activity="share_disc", name="Mina", gender="girl", companion="fox", trait="kind"),
    StoryParams(place="market", activity="share_disc", name="Jem", gender="boy", companion="crow", trait="quick-witted"),
    StoryParams(place="oak", activity="spin_disc", name="Nora", gender="girl", companion="goat", trait="merry"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
