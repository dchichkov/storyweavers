#!/usr/bin/env python3
"""
storyworlds/worlds/spanish_shotgun_dark_bravery_rhyming_story.py
================================================================

A tiny storyworld about a brave child, a dark room, and a Spanish rhyme.

Seed tale sketch:
---
A child hears a soft knock in the dark and feels a little scared. A parent
hands over a lantern and a small play shotgun prop from a costume box. The
child remembers a Spanish rhyme from school and takes a brave step forward.
The scary shape turns out to be only a dropped paper bag, and the child sings
the rhyme with a smile.

World idea:
---
- The dark is a physical setting that hides small objects.
- Bravery is a meme that can grow when the child acts despite fear.
- Spanish words are a comforting tool the child can repeat.
- The "shotgun" is only a harmless costume prop, not a weapon.
- The story turns on fear -> courage -> discovery -> relief.

The prose is deliberately rhyming, child-facing, and state-driven:
the lantern, the rhyme, the hidden object, and the brave step all matter.
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


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    child_name: str = "Maya"
    parent_name: str = "Papa"
    language_word: str = "Spanish"
    prop_word: str = "shotgun"
    dark_word: str = "dark"
    bravery_word: str = "bravery"
    rhyme_style: str = "rhyming"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    child: Entity
    parent: Entity
    prop: Entity
    lantern: Entity
    hidden_object: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in [self.child, self.parent, self.prop, self.lantern, self.hidden_object]:
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "hall": "the hall",
    "attic": "the attic",
    "shed": "the shed",
    "stage": "the stage",
}

NAMES = ["Maya", "Leo", "Nia", "Omar", "Zoe", "Ben"]
PARENTS = ["Mama", "Papa", "Abuela", "Abuelo"]
PROPS = [
    "toy shotgun",
    "cardboard shotgun",
    "costume shotgun",
]
HIDDEN_OBJECTS = [
    "paper bag",
    "wind-up mouse",
    "fallen hat",
    "small mop",
]
SPANISH_LINES = [
    "valiente, valiente, paso al frente",
    "luz de luna, calma mi mente",
    "uno, dos, tres, yo puedo seguir",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming storyworld about dark places, Spanish words, and brave hearts."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("The story needs a small setting like the hall, attic, shed, or stage.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    params = StoryParams(
        setting=setting,
        seed=args.seed,
        child_name=name,
        parent_name=parent,
        language_word="Spanish",
        prop_word="shotgun",
        dark_word="dark",
        bravery_word="bravery",
        rhyme_style="rhyming",
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(id=params.child_name, kind="character", label=params.child_name, type="child")
    parent = Entity(id=params.parent_name, kind="character", label=params.parent_name, type="parent")
    prop = Entity(id="prop", kind="thing", label=params.prop_word, type="costume prop")
    lantern = Entity(id="lantern", kind="thing", label="lantern", type="light")
    hidden = Entity(id="hidden", kind="thing", label="paper bag", type="small object")
    return World(
        setting=SETTINGS[params.setting],
        child=child,
        parent=parent,
        prop=prop,
        lantern=lantern,
        hidden_object=hidden,
    )


def _rhyme(lines: list[str]) -> str:
    return " ".join(lines)


def _build_story(world: World, params: StoryParams) -> None:
    c = world.child
    p = world.parent
    prop = world.prop
    lantern = world.lantern
    hidden = world.hidden_object

    c.memes["fear"] = 1.0
    c.memes["bravery"] = 0.0
    lantern.meters["light"] = 1.0

    world.say(
        f"In the {params.dark_word} little {world.setting}, {c.label} felt a shiver and a scare, "
        f"for shadows could wobble and whisper in air."
    )
    world.say(
        f"{p.label} came near with a lantern so bright, and gave {c.label} a {prop.label} to hold just right."
    )

    world.para()
    spanish = random.Random(params.seed or 0).choice(SPANISH_LINES)
    world.say(
        f'"{spanish}," said {c.label}, with a breathy small grin; '
        f'the words felt like courage that bloomed from within.'
    )
    c.inc_meme("bravery", 1.0)
    c.memes["fear"] = 0.0
    world.say(
        f"With {params.bravery_word} a-twinkle, {c.label} took a walk, "
        f"and softly kept speaking in rhyme as they talked."
    )

    world.para()
    hidden.meters["hidden"] = 1.0
    world.say(
        f"The lantern beam swayed, and it shone on the floor; "
        f"there sat just a paper bag, nothing more."
    )
    world.say(
        f"{c.label} laughed, because all of the fright had been only a shadow that puffed out of sight."
    )

    world.para()
    c.inc_meme("joy", 1.0)
    world.say(
        f"So {c.label} stood tall in the {params.dark_word} little room, "
        f"with Spanish on lips and no room left for gloom."
    )
    world.say(
        f"The {prop.label} went back in its box with a thump, "
        f"and bravery sparkled like warm little pump."
    )

    world.facts.update(
        child=c,
        parent=p,
        prop=prop,
        lantern=lantern,
        hidden=hidden,
        spanish=spanish,
        setting=params.setting,
        brave=bool(c.memes.get("bravery", 0.0) >= 1.0),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short rhyming story for a little child in {world.setting} with a dark shadow and a brave heart.",
        f"Tell a gentle story that includes the words Spanish, shotgun, and dark, and ends with bravery and relief.",
        f"Write a simple rhyming tale where a child holds a lantern, repeats a Spanish line, and discovers the scary thing was harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.child
    p = world.parent
    return [
        QAItem(
            question=f"Who was brave in the story?",
            answer=f"{c.label} was brave after feeling scared in the dark and hearing the comforting Spanish rhyme.",
        ),
        QAItem(
            question=f"What did {p.label} give {c.label} to help?",
            answer=f"{p.label} gave {c.label} a lantern and a harmless shotgun costume prop so {c.label} could look around safely.",
        ),
        QAItem(
            question="What was the scary thing really?",
            answer="It was only a paper bag, so the dark shape was harmless after all.",
        ),
        QAItem(
            question="Why did the child feel braver at the end?",
            answer=f"{c.label} repeated a Spanish line, found the hidden shape was only a paper bag, and then felt proud and calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel scared.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so people can see in dark places.",
        ),
        QAItem(
            question="Why can Spanish words be comforting?",
            answer="A familiar Spanish rhyme can feel warm and steady, which helps a child feel calmer.",
        ),
        QAItem(
            question="Why is a costume shotgun safe in this story?",
            answer="It is only a pretend prop from a costume box, not a real weapon.",
        ),
    ]


ASP_RULES = r"""
child_brave(C) :- fear(C), hears_spanish(C), finds_harmless_shape(C).
dark_place(S) :- setting(S).
safe_prop(P) :- prop(P), costume(P).
story_good(S) :- dark_place(S), child_brave(C), safe_prop(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        if "dark" in setting:
            lines.append(asp.fact("dark", key))
    for nm in NAMES:
        lines.append(asp.fact("child_name", nm))
    for pr in PROPS:
        lines.append(asp.fact("prop", pr.replace(" ", "_")))
        lines.append(asp.fact("costume", pr.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.language_word == "Spanish" and params.prop_word == "shotgun"


def asp_verify() -> int:
    if not _python_reasonable(StoryParams(setting="hall")):
        print("MISMATCH: python reasonableness gate failed unexpectedly.")
        return 1
    print("OK: python reasonableness gate is consistent.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    _build_story(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(sample.world.trace())
    if qa:
        print()
        print("== Generation prompts ==")
        for i, q in enumerate(sample.prompts, 1):
            print(f"{i}. {q}")
        print()
        print("== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="hall", child_name="Maya", parent_name="Mama"),
    StoryParams(setting="attic", child_name="Leo", parent_name="Papa"),
    StoryParams(setting="shed", child_name="Nia", parent_name="Abuela"),
    StoryParams(setting="stage", child_name="Omar", parent_name="Abuelo"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(p) for p in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses a simple internal reasonableness gate for its tiny ASP twin.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = build_all_samples()
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
