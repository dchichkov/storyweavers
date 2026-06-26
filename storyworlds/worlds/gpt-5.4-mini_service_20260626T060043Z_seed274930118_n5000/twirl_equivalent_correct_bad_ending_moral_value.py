#!/usr/bin/env python3
"""
storyworlds/worlds/twirl_equivalent_correct_bad_ending_moral_value.py
=====================================================================

A small Tall Tale story world about a twirl, an equivalent replacement,
a correct choice, and the difference between a Bad Ending, a Moral Value,
and a Happy Ending.

Seed premise:
---
A child with a treasured spinning top loves to twirl it until a tricky gust
knocks it into a muddy ditch. A grown-up warns that if they chase the shiny,
wrong-looking top, they will end up with a Bad Ending. The child must choose
the correct equivalent object: the same-top-but-clean version, repaired and
made right by a careful helper. The story turns on whether the hero values
showy luck or moral value: patience, honesty, and a truthful fix.

World model:
---
- The hero has joy, worry, pride, and humility.
- A treasured object can be damaged, lost, or replaced by an equivalent.
- A helper can judge whether a replacement is correct.
- The bad path increases worry and shame; the correct path restores pride,
  joy, and trust.

This script supports the standard storyworld interface, QA output, JSON, trace,
and an inline ASP twin for parity checking.
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
# World entities
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
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the county fair"


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    requires: str  # what makes the replacement correct: "clean", "fixed", "matched"


@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
    "fair": Setting(place="the county fair"),
    "barn": Setting(place="the old barn"),
    "dock": Setting(place="the river dock"),
    "green": Setting(place="the town green"),
}

TREASURES = {
    "top": Treasure(
        label="spinning top",
        phrase="a brass spinning top with a painted stripe",
        type="top",
        requires="clean and balanced",
    ),
    "kite": Treasure(
        label="kite",
        phrase="a bright kite with a long tail",
        type="kite",
        requires="patched and whole",
    ),
    "boot": Treasure(
        label="boot",
        phrase="one sturdy boot with a silver buckle",
        type="boot",
        requires="clean and matched",
    ),
}

HELPERS = {
    "clockmaker": "the clockmaker",
    "aunt": "Aunt June",
    "carpenter": "the carpenter",
    "teacher": "the teacher",
}

NAMES = {
    "girl": ["Mabel", "June", "Ada", "Nell", "Ruby", "Pearl"],
    "boy": ["Milo", "Otis", "Cal", "Hank", "Jasper", "Eli"],
}

TRAITS = ["brave", "curious", "patient", "honest", "spry", "stubborn"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def correct_replacement(treasure: Treasure) -> str:
    return {
        "top": "another brass top that spun true",
        "kite": "a patched kite that matched the old one",
        "boot": "the missing boot, cleaned to shine like the first",
    }[treasure.type]


def equivalent(treasure: Treasure) -> str:
    return f"an equivalent {treasure.label}"


def bad_ending_line(hero: Entity) -> str:
    return (
        f"If {hero.id} chose the shiny wrong thing, the day would end in a Bad Ending, "
        f"with fuss, mud, and a knot in the heart."
    )


def moral_value_line() -> str:
    return "The Moral Value was plain: the correct choice is the one that tells the truth."


def happy_ending_line(hero: Entity, helper: Entity, treasure: Entity) -> str:
    return (
        f"In the Happy Ending, {hero.id} walked home with {hero.pronoun('possessive')} "
        f"{treasure.label} held safe, and {helper.label} laughed like a bell in the wind."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=HELPERS[params.helper]))
    treasure = world.add(Entity(
        id="treasure",
        type=params.treasure,
        label=TREASURES[params.treasure].label,
        phrase=TREASURES[params.treasure].phrase,
        owner=hero.id,
        caretaker=helper.id,
        meters={"clean": 1.0, "whole": 1.0, "true": 1.0},
        memes={"value": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, treasure=treasure, params=params)

    # Act 1: tall-tale setup
    world.say(
        f"{hero.id} was a {params.trait} little {hero.type} who loved to twirl {hero.pronoun('possessive')} {treasure.label} "
        f"until it flashed like a coin in the sun."
    )
    world.say(
        f"At {world.setting.place}, everybody knew {hero.id}'s {treasure.label} was not just any toy; "
        f"it was the sort of thing that made the air seem bigger."
    )

    # Act 2: trouble and choice
    world.para()
    world.say(
        f"One gust of wind sent the {treasure.label} skittering away, and it came back muddy and bent, which was no good at all."
    )
    world.say(
        f"{helper.label} pointed to the mess and said, \"That first look is a trick. The shiny wrong one is not equivalent.\""
    )
    world.say(bad_ending_line(hero))
    world.say(moral_value_line())

    # Act 3: correction and resolution
    world.para()
    world.say(
        f"{hero.id} took a slow breath, wiped the dirt away, and chose the {treasure.label} that was {TREASURES[params.treasure].requires}."
    )
    world.say(
        f"That was the correct choice: {correct_replacement(treasure)}."
    )
    world.say(
        f"The clean replacement and the repaired treasure were equivalent in the way that mattered, because both kept the promise of the original."
    )
    world.say(
        f"Then {hero.id} twirled {treasure.it()} again, and this time it sang a bright little song instead of wobbling."
    )
    world.say(happy_ending_line(hero, helper, treasure))

    hero.memes["joy"] = 2.0
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0
    helper.memes["approval"] = 1.0
    treasure.meters["clean"] = 1.0
    treasure.meters["whole"] = 1.0
    treasure.meters["true"] = 1.0
    world.facts["resolved"] = True
    world.facts["equivalent"] = correct_replacement(treasure)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, treasure = f["hero"], f["treasure"]
    return [
        f'Write a Tall Tale for children about {hero.id} and a twirl, where the correct fix is an equivalent {treasure.label}.',
        f"Tell a story that includes the words twirl, equivalent, and correct, and ends with a Happy Ending instead of a Bad Ending.",
        f"Write a gentle fairground tale about choosing the moral value of honesty when a treasured {treasure.label} gets lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, treasure = f["hero"], f["helper"], f["treasure"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do with the {treasure.label} at {world.setting.place}?",
            answer=f"{hero.id} loved to twirl {hero.pronoun('possessive')} {treasure.label} until it flashed and spun.",
        ),
        QAItem(
            question=f"Why did {helper.label} say the shiny wrong one was not equivalent?",
            answer="Because it only looked good for a moment, but it did not keep the promise of the original treasure.",
        ),
        QAItem(
            question="What made the ending a Happy Ending instead of a Bad Ending?",
            answer=f"{hero.id} chose the correct replacement and fixed the treasure truthfully, so the day ended with joy instead of trouble.",
        ),
        QAItem(
            question="What was the moral value of the story?",
            answer="The moral value was that honesty and a correct choice matter more than a shiny mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does equivalent mean?",
            answer="Equivalent means two things match in the way that matters, even if they do not look exactly the same.",
        ),
        QAItem(
            question="What does correct mean?",
            answer="Correct means right for the problem, not just pretty or quick.",
        ),
        QAItem(
            question="What is a twirl?",
            answer="A twirl is a quick spinning turn, like a top or a dancer makes.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
chosen_correct(T) :- treasure(T), requires(T, clean_and_balanced), correct_choice(T).
chosen_correct(T) :- treasure(T), requires(T, patched_and_whole), correct_choice(T).
chosen_correct(T) :- treasure(T), requires(T, clean_and_matched), correct_choice(T).

bad_ending :- wrong_choice(T), treasure(T).
happy_ending :- chosen_correct(T).

moral_value(honesty).
correct_choice(T) :- treasure(T), not wrong_choice(T).
equivalent(T) :- chosen_correct(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("place_name", pid, setting.place))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("requires", tid, t.requires.replace(" ", "_")))
    for hid in HELPER_NAMES:
        lines.append(asp.fact("helper_kind", hid))
    return "\n".join(lines)


HELPER_NAMES = list(HELPERS.keys())


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.solve(asp_program("#show happy_ending/0.\n#show bad_ending/0.\n#show moral_value/1.\n#show equivalent/1.\n"), models=1)
    if not models:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP twin loads and solves a model.")
    return 0


# ---------------------------------------------------------------------------
# Serialization helpers and CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fair", treasure="top", name="Mabel", gender="girl", helper="clockmaker", trait="brave"),
    StoryParams(place="barn", treasure="kite", name="Milo", gender="boy", helper="carpenter", trait="honest"),
    StoryParams(place="dock", treasure="boot", name="June", gender="girl", helper="aunt", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale story world: twirl, equivalent, correct, and a moral ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, treasure=treasure, name=name, gender=gender, helper=helper, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show equivalent/1.\n#show bad_ending/0.\n#show happy_ending/0.\n#show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available; this world's twin is intentionally small and deterministic.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.treasure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
