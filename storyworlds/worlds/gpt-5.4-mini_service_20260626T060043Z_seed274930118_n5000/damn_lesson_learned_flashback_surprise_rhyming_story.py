#!/usr/bin/env python3
"""
storyworlds/worlds/damn_lesson_learned_flashback_surprise_rhyming_story.py
===========================================================================
A small standalone storyworld for a rhyming, lesson-learned tale with a
flashback and a surprise turn.

Premise:
A child is trying to build a little creek dam. The wall keeps wobbling, the
child blurts a rude word, and a kind parent helps them find a calmer rhyme.
A flashback reveals an earlier lesson, and a surprise ending shows the dam
standing strong only after the child changes the way they speak and build.

This world is deliberately small: one setting, one activity, one prize, one
lesson path. The simulation tracks physical meters and emotional memes so the
story is driven by world state instead of a frozen paragraph.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the creek"
    affords: set[str] = field(default_factory=lambda: {"build_dam"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = "damn"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str


@dataclass
class Lesson:
    old_word: str
    kinder_word: str
    rhyme: str
    flashback_line: str
    surprise_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


@dataclass
class StoryParams:
    name: str = "Nia"
    gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None


SETTING = Setting()
ACTIVITY = Activity(
    id="build_dam",
    verb="build a little dam",
    gerund="building a little dam",
    rush="dash to the creek stones",
    mess="soggy",
    soil="wobbly and soggy",
    keyword="damn",
    tags={"dam", "lesson", "flashback", "surprise", "rhyming"},
)
PRIZE = Prize(
    label="sand bucket",
    phrase="a shiny red sand bucket",
    type="bucket",
    region="hand",
)
LESSON = Lesson(
    old_word="damn",
    kinder_word="darn",
    rhyme="When words go rough, make kinder sounds; soft words help hearts and fix up grounds.",
    flashback_line="She flashed back to last spring, when a sharp word made her cousin cry by the swing.",
    surprise_line="The surprise was sweet: the creek held its shape because calm words and careful stones worked as a team in the street.",
)

GIRL_NAMES = ["Nia", "Mina", "Luna", "Pia", "Zara"]
BOY_NAMES = ["Owen", "Milo", "Eli", "Jude", "Kai"]
PARENTS = ["mother", "father"]


def _act(world: World, hero: Entity, prize: Entity) -> None:
    hero.meters["effort"] += 1
    world.say(
        f"{hero.id} ran to the creek with {hero.pronoun('possessive')} {prize.label}, "
        f"ready to {ACTIVITY.verb} and make a neat little peak."
    )
    world.say(
        f"The first pile of stones slid in the mud, and the water gave a scoff and a leak."
    )
    hero.memes["frustration"] += 1
    hero.meters["wobble"] += 1


def _warning(world: World, parent: Entity, hero: Entity) -> None:
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type if parent.type else 'parent'} said, "
        f'“Easy now, sweet pea. No harsh words in a sour little spree.”'
    )
    hero.memes["shame"] += 1


def _flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"Then {hero.id} had a flashback with a tiny sting and a tiny ring: "
        f"{LESSON.flashback_line}"
    )


def _surprise(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.meters["care"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} took a breath and said, “{LESSON.kinder_word},” instead of the old sharp thing."
    )
    world.say(
        f"{LESSON.rhyme}"
    )
    world.say(
        f"They packed flat stones and packed them tight, then tucked in sand to hold them right."
    )
    prize.meters["wet"] = 0
    prize.meters["safe"] = 1
    world.say(
        f"The surprise was bright: the little dam stood tall at last, and {parent.id} smiled in the fading light."
    )
    world.say(
        f"{hero.id} grinned and learned a simple clue: soft words can help, and careful hands can too."
    )
    world.facts["lesson"] = LESSON
    world.facts["resolved"] = True


def tell(name: str, gender: str, parent_type: str) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="bucket", type="bucket", label="sand bucket", caretaker=parent.id))

    world.say(
        f"{hero.id} loved the creek and loved the day, and loved to stack up stones in play."
    )
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} {prize.label} tight, ready to build a dam just right."
    )

    world.para()
    _act(world, hero, prize)
    _warning(world, parent, hero)
    world.say(
        f"{hero.id} almost blurted “{LESSON.old_word},” but caught {hero.pronoun('object')} quick and bit {hero.pronoun('possessive')} lip."
    )
    _flashback(world, hero)

    world.para()
    _surprise(world, hero, parent, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=ACTIVITY, setting=SETTING)
    return world


def valid_choices() -> list[tuple[str, str]]:
    return [(SETTING.place, ACTIVITY.id)]


def explain_rejection() -> str:
    return "(No story: this world only supports the creek dam lesson and its rhyming flashback-surprise turn.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short rhyming story for a young child about {hero.id} building a tiny dam at the creek.',
        f"Tell a gentle lesson-learned story where {hero.id} almost says the word '{LESSON.old_word}' but chooses a kinder rhyme instead.",
        f"Write a flashback-and-surprise story that ends with a safe little dam and a happy new word.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize = f["hero"], f["parent"], f["prize"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to build at the creek?",
            answer=f"{hero.id} was trying to build a little dam with stones and {prize.label} sand.",
        ),
        QAItem(
            question=f"What word did {hero.id} almost say when the dam got wobbly?",
            answer=f"{hero.id} almost said '{LESSON.old_word}', but caught {hero.pronoun('object')} and chose '{LESSON.kinder_word}' instead.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} to do?",
            answer=f"The flashback reminded {hero.id} to use kinder words and calmer hands, because harsh words can sting.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer="The surprise was that the little dam finally held together after the child used careful stones and a softer word.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and peaceful, because the job was done and the lesson had been learned.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dam?",
            answer="A dam is a wall or barrier built to hold back water or slow it down.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that jumps back to something that happened before.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is an unexpected turn that makes the ending feel special or new.",
        ),
        QAItem(
            question="Why do kinder words matter?",
            answer="Kinder words matter because they help people feel safe, calm, and respected.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(creek).
activity(build_dam).
valid_story(creek, build_dam).

"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "creek"),
            asp.fact("activity", "build_dam"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_choices())
    asp_set = {(a, b) for (a, b) in asp_valid_combos()}
    if py == asp_set:
        print(f"OK: clingo gate matches valid_choices() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld with lesson, flashback, and surprise.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.gender is None:
        args.gender = rng.choice(["girl", "boy"])
    if args.name is None:
        args.name = rng.choice(GIRL_NAMES if args.gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=args.name, gender=args.gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story combo:")
        print("  creek build_dam")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            name=args.name or "Nia",
            gender=args.gender or "girl",
            parent=args.parent or "mother",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
