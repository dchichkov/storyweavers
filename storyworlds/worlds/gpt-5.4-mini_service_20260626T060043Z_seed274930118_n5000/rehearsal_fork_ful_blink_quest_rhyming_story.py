#!/usr/bin/env python3
"""
storyworlds/worlds/rehearsal_fork_ful_blink_quest_rhyming_story.py
===================================================================

A small standalone storyworld about a rehearsal quest: a child carries a
fork-ful treat, a stage light blinks, and the group finds a careful fix.

The world is intentionally compact:
- one rehearsal setting
- one hero
- one helpful partner
- one fragile snack
- one small quest

The prose aims for a rhyming-story feel: soft, sing-song, concrete, and
child-facing, while still being driven by simulated state.
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
    place: str = "the rehearsal hall"
    afford: str = "rehearsal"


@dataclass
class Snack:
    label: str
    phrase: str
    forkful: bool = True
    fragile: bool = True


@dataclass
class QuestGear:
    label: str
    phrase: str
    helps: str
    protects: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hall": Setting(place="the rehearsal hall"),
    "stage": Setting(place="the little stage"),
    "classroom": Setting(place="the classroom corner"),
}

SNACKS = {
    "pie": Snack(label="pie", phrase="a sweet berry pie"),
    "cake": Snack(label="cake", phrase="a tiny moon cake"),
    "tart": Snack(label="tart", phrase="a tart with shiny jam"),
}

QUEST_GEAR = {
    "napkin": QuestGear(
        label="napkin",
        phrase="a clean napkin",
        helps="hold the treat steady",
        protects="catch drips",
    ),
    "tray": QuestGear(
        label="tray",
        phrase="a small tray",
        helps="carry the snack straight",
        protects="keep it level",
    ),
    "spoon": QuestGear(
        label="spoon",
        phrase="a shiny spoon",
        helps="lift smaller bites",
        protects="make tiny bites easier",
    ),
}

HERO_NAMES = ["Mina", "Pip", "Nora", "Ben", "Luna", "Toby"]
HELPER_NAMES = ["Dot", "Milo", "Tess", "Jory", "Ada"]
TRAITS = ["brave", "bright", "bouncy", "gentle", "cheery"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    snack: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
def is_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.snack in SNACKS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    snack = args.snack or rng.choice(list(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = "girl" if gender == "boy" else "boy"

    if args.snack and args.snack not in SNACKS:
        raise StoryError("Unknown snack choice.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting choice.")

    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    trait = rng.choice(TRAITS)
    params = StoryParams(
        place=place,
        snack=snack,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )
    if not is_reasonable(params):
        raise StoryError("Those options do not make a workable rehearsal quest.")
    return params


def predict_spill(world: World, hero: Entity, snack: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["nervous"] = 1.0
    sim.facts["blink"] = True
    return True if snack.meters.get("spill", 0.0) >= 1.0 else False


def setup(world: World, hero: Entity, helper: Entity, snack: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'bright')} little {hero.type} "
        f"at {world.setting.place}, ready for a rehearsal quest."
    )
    world.say(
        f"{hero.id} loved the song and the step-tap beat, and {helper.id} liked to "
        f"help with every neat little feat."
    )
    world.say(
        f"Before the scene, {helper.id} brought {hero.pronoun('object')} {snack.phrase}, "
        f"and {hero.id} held {snack.label} like treasure on a plate."
    )


def begin_quest(world: World, hero: Entity, snack: Entity) -> None:
    hero.memes["excited"] = 1.0
    world.say(
        f"The Quest was simple but funny: carry the fork-ful treat to the prop table "
        f"without a drip or a sneezy slip."
    )
    world.say(
        f"{hero.id} tried to walk slow and straight, but the fork-ful wobbled at the edge "
        f"of the fork like a boat on a shiny lake."
    )


def blink_turn(world: World, hero: Entity, snack: Entity) -> None:
    hero.memes["nervous"] = 1.0
    snack.meters["wobble"] = 1.0
    world.say(
        f"Then a stage light gave a blink, bright as a wink, and {hero.id} went frozen "
        f"for just one second of think."
    )
    world.say(
        f"The fork dipped low, the berry glow trembled slow, and a little dab of jam "
        f"tried to go."
    )
    snack.meters["spill"] = 1.0
    world.say(
        f"{hero.id} did not want a mess on the dress, so {hero.pronoun()} whispered, "
        f"\"Oh dear, not this!\""
    )


def fix_quest(world: World, hero: Entity, helper: Entity, snack: Entity) -> None:
    gear = world.add(Entity(
        id="napkin",
        kind="thing",
        type="gear",
        label=QUEST_GEAR["napkin"].label,
        phrase=QUEST_GEAR["napkin"].phrase,
        owner=hero.id,
    ))
    hero.memes["calm"] = 1.0
    helper.memes["kind"] = 1.0
    snack.meters["spill"] = 0.0
    snack.meters["wobble"] = 0.0
    world.say(
        f"Then {helper.id} smiled and said, \"Use {gear.label} light, and hold it tight; "
        f"we can still finish this quest tonight.\""
    )
    world.say(
        f"{hero.id} wrapped the fork-ful in {gear.phrase}, took one careful step, then two, "
        f"and the wobble slid away like morning dew."
    )
    world.say(
        f"At the last small table, the treat stayed neat, and {hero.id} gave a proud little nod: "
        f"the Quest was complete, sweet and fleet."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        meters={"balance": 1.0},
        memes={"trait_word": params.trait},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
    ))
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label=SNACKS[params.snack].label,
        phrase=SNACKS[params.snack].phrase,
        owner=hero.id,
        caretaker=helper.id,
        meters={"wobble": 0.0, "spill": 0.0},
    ))

    setup(world, hero, helper, snack)
    world.say("")
    begin_quest(world, hero, snack)
    blink_turn(world, hero, snack)
    fix_quest(world, hero, helper, snack)
    world.facts = {
        "hero": hero,
        "helper": helper,
        "snack": snack,
        "setting": world.setting,
        "params": params,
        "quest": "rehearsal quest",
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    return [
        f'Write a short rhyming story about a rehearsal quest with a fork-ful of {snack.label}.',
        f"Tell a gentle story where {hero.id} and {helper.id} keep a sweet treat steady during a rehearsal.",
        f"Write a child-friendly story that includes the words rehearsal, fork-ful, blink, and Quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Where did {hero.id} begin the Quest?",
            answer=f"{hero.id} began the Quest at {place}, during a rehearsal with {helper.id}.",
        ),
        QAItem(
            question=f"What was {hero.id} carrying on the fork?",
            answer=f"{hero.id} was carrying a fork-ful of {snack.phrase}.",
        ),
        QAItem(
            question="What made the treat wobble?",
            answer="A stage light blink made the hero freeze for a moment, and the fork-ful wobbled.",
        ),
        QAItem(
            question=f"How did {helper.id} help at the end?",
            answer=f"{helper.id} suggested a napkin and helped {hero.id} keep the treat steady.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rehearsal?",
            answer="A rehearsal is a practice run for a play, song, or performance before the real show.",
        ),
        QAItem(
            question="What is a fork-ful?",
            answer="A fork-ful is the amount of food that fits on one forkful bite.",
        ),
        QAItem(
            question="What does blink mean?",
            answer="A blink is a very quick closing and opening of the eyes, or a quick flash of light.",
        ),
        QAItem(
            question="What is a Quest?",
            answer="A Quest is a quest or journey with a goal to reach, often like a small adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
rehearsal_place(hall).
rehearsal_place(stage).
rehearsal_place(classroom).

snack(pie).
snack(cake).
snack(tart).

reasonable(Place, Snack) :- rehearsal_place(Place), snack(Snack).
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("rehearsal_place", place))
    for snack in SNACKS:
        lines.append(asp.fact("snack", snack))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {(place, snack) for place in SETTINGS for snack in SNACKS}
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between clingo and Python gates.")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming rehearsal-Quest storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(place="hall", snack="pie", hero_name="Mina", hero_gender="girl", helper_name="Dot", helper_gender="boy", trait="bouncy"),
    StoryParams(place="stage", snack="cake", hero_name="Pip", hero_gender="boy", helper_name="Tess", helper_gender="girl", trait="gentle"),
    StoryParams(place="classroom", snack="tart", hero_name="Luna", hero_gender="girl", helper_name="Milo", helper_gender="boy", trait="cheery"),
]


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_reasonable()
        for place, snack in combos:
            print(place, snack)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_from_args(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
