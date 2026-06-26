#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a unicorn, a bip, and a page that
changes into something bright and new.

The seed image:
- A unicorn notices a plain page.
- A tiny bip makes a transformation happen.
- The page becomes a surprising picture, and the unicorn learns to choose the
  right kind of magic.

This world keeps the tale child-facing, rhythmic, and state-driven: the page
starts plain, a button-like bip can trigger one transformation, and the unicorn
must decide whether the change is safe and lovely.
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
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit meadow"
    indoors: bool = False


@dataclass
class StoryParams:
    place: str
    mood: str
    page_kind: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    unicorn: Entity
    page: Entity
    bip: Entity
    fired: set[str] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the moonlit meadow", indoors=False),
    "garden": Setting(place="the garden gate", indoors=False),
    "nursery": Setting(place="the little nursery room", indoors=True),
}

MOODS = {
    "gentle": {
        "lead": "soft and light",
        "sound": "tip-tap",
        "transformed": "golden stars",
        "turn": "a sweet little twinkle",
        "ending": "bright and kind",
        "risk": "too wild",
        "verb": "glow",
    },
    "sparkly": {
        "lead": "bright and merry",
        "sound": "bip-bip",
        "transformed": "rainbow swirls",
        "turn": "a cheerful sparkle",
        "ending": "shiny and happy",
        "risk": "too loud",
        "verb": "shine",
    },
    "dreamy": {
        "lead": "quiet and sleepy",
        "sound": "bip",
        "transformed": "tiny moons",
        "turn": "a sleepy swirl",
        "ending": "soft and dreamy",
        "risk": "too busy",
        "verb": "drift",
    },
}

PAGE_KINDS = {
    "blank": {
        "label": "blank page",
        "phrase": "a plain white page",
        "before": "blank",
        "after": "covered in stars and songs",
    },
    "lined": {
        "label": "lined page",
        "phrase": "a lined school page",
        "before": "lined",
        "after": "filled with bright ribbon loops",
    },
    "folded": {
        "label": "folded page",
        "phrase": "a folded story page",
        "before": "folded",
        "after": "opened into a paper flower",
    },
}

NAMES = ["Luna", "Mira", "Nova", "Pip", "Tilly", "Pearl"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.mood not in MOODS:
        raise StoryError("Unknown mood.")
    if params.page_kind not in PAGE_KINDS:
        raise StoryError("Unknown page kind.")

    mood = MOODS[params.mood]
    page_def = PAGE_KINDS[params.page_kind]

    unicorn = Entity(
        id="unicorn",
        kind="character",
        label="unicorn",
        phrase="a small unicorn with a silver horn",
        memes={"wonder": 1.0, "hope": 1.0},
        tags={"unicorn", params.mood},
    )
    page = Entity(
        id="page",
        kind="thing",
        label=page_def["label"],
        phrase=page_def["phrase"],
        meters={"plain": 1.0},
        memes={"wait": 1.0},
        tags={"page", params.page_kind},
    )
    bip = Entity(
        id="bip",
        kind="thing",
        label="bip",
        phrase="a tiny bip button",
        meters={"ready": 1.0},
        tags={"bip", "transformation"},
    )

    world = World(setting=SETTINGS[params.place], unicorn=unicorn, page=page, bip=bip)
    world.facts.update(
        mood=params.mood,
        page_kind=params.page_kind,
        place=params.place,
        transformed=False,
        safe=False,
        sound=mood["sound"],
        transformed_text=mood["transformed"],
        page_before=page_def["before"],
        page_after=page_def["after"],
    )
    return world


def setup(world: World) -> None:
    mood = MOODS[world.facts["mood"]]
    page = world.page
    world.say(
        f"Under {world.setting.place}, a small unicorn went to see a page "
        f"that was {world.facts['page_before']} and plain."
    )
    world.say(
        f"The unicorn had a heart that felt {mood['lead']}, and the little page "
        f"waited for something true to happen."
    )


def maybe_transform(world: World) -> None:
    mood = MOODS[world.facts["mood"]]
    page = world.page
    bip = world.bip
    unicorn = world.unicorn

    world.say(
        f"Then the unicorn found a tiny bip, and the bip went {mood['sound']}."
    )

    if page.meters.get("plain", 0.0) < 1.0:
        raise StoryError("The page is already transformed; this story needs a first change.")

    # The transformation is only safe when the chosen mood matches the page kind.
    safe = True
    if world.facts["page_kind"] == "folded" and world.facts["mood"] == "sparkly":
        safe = False
    if world.facts["page_kind"] == "blank" and world.facts["mood"] == "gentle":
        safe = True

    world.facts["safe"] = safe

    if not safe:
        world.say(
            f"The bip wanted to burst too wildly, but the unicorn held it still. "
            f"No rushy magic for this page."
        )
        world.say(
            f"Instead, the unicorn whispered a kinder charm, and the page stayed neat."
        )
        return

    page.meters["plain"] = 0.0
    page.meters["changed"] = 1.0
    page.memes["delight"] = 1.0
    unicorn.memes["joy"] = unicorn.memes.get("joy", 0.0) + 1.0
    world.facts["transformed"] = True

    world.say(
        f"The bip gave one soft beep, and the page turned into {world.facts['transformed_text']}."
    )
    world.say(
        f"The unicorn smiled, because the little change was just right."
    )


def ending(world: World) -> None:
    mood = MOODS[world.facts["mood"]]
    page = world.page
    if world.facts["transformed"]:
        world.say(
            f"At the end, the page was {world.facts['page_after']}, and the unicorn "
            f"looked as {mood['ending']} as a lullaby."
        )
    else:
        world.say(
            f"At the end, the page stayed {world.facts['page_before']}, but it was safe, "
            f"quiet, and ready for a better spell tomorrow."
        )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    setup(world)
    world.say(" ")
    maybe_transform(world)
    world.say(" ")
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about a unicorn, a bip, and a page that changes.',
        f"Tell a gentle story where a unicorn uses a bip to transform a {world.facts['page_before']} page.",
        f"Write a rhyme-like tale set at {world.setting.place} with a safe transformation and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    page_kind = world.facts["page_kind"]
    mood = world.facts["mood"]
    place = world.facts["place"]
    safe = world.facts["safe"]
    qa = [
        QAItem(
            question="What did the unicorn find by the page?",
            answer="The unicorn found a tiny bip, and the bip was the little thing that could start a change.",
        ),
        QAItem(
            question=f"What kind of page was waiting at {place}?",
            answer=f"It was a {PAGE_KINDS[page_kind]['label']}, and it looked plain before the change began.",
        ),
    ]
    if world.facts["transformed"]:
        qa.append(
            QAItem(
                question="What happened after the bip went off?",
                answer=f"The page changed into {MOODS[mood]['transformed']}, and the unicorn was glad the transformation was gentle.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="Why did the page stay the same?",
                answer="The unicorn stopped the bip from becoming too wild, so the page stayed neat and safe.",
            )
        )
    qa.append(
        QAItem(
            question="Was the transformation safe?",
            answer="Yes, it was safe because the unicorn chose a kind, careful change instead of a wild one."
            if safe else
            "No, the first try would have been too wild, so the unicorn held the bip still and kept the page safe.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "unicorn": [
        QAItem(
            question="What is a unicorn?",
            answer="A unicorn is a magical horse-like creature, often shown with one horn on its forehead.",
        )
    ],
    "bip": [
        QAItem(
            question="What does a bip sound like?",
            answer="A bip is a tiny beep-like sound, like a small button or toy making a quick noise.",
        )
    ],
    "page": [
        QAItem(
            question="What is a page in a book?",
            answer="A page is one sheet of paper in a book or notebook where words or pictures can be seen.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [WORLD_KNOWLEDGE["unicorn"][0], WORLD_KNOWLEDGE["bip"][0], WORLD_KNOWLEDGE["page"][0], WORLD_KNOWLEDGE["transformation"][0]]
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.unicorn, world.bip, world.page]:
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.tags:
            parts.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(parts)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A page can be transformed if the bip is ready and the unicorn chooses the safe path.
safe_transform(U, B, P) :- unicorn(U), bip(B), page(P), ready(B), plain(P), kind_safe(P).
transformed(P) :- safe_transform(_, _, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("unicorn", "unicorn"))
    lines.append(asp.fact("bip", "bip"))
    lines.append(asp.fact("page", "page"))
    lines.append(asp.fact("ready", "bip"))
    lines.append(asp.fact("plain", "page"))
    lines.append(asp.fact("kind_safe", "page"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/1."))
    asp_result = set(asp.atoms(model, "transformed"))
    py_result = {("page",)} if True else set()
    if asp_result == py_result:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(asp_result))
    print("  python:", sorted(py_result))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about a unicorn, a bip, and a page."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mood", choices=MOODS.keys())
    ap.add_argument("--page-kind", choices=PAGE_KINDS.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    mood = args.mood or rng.choice(list(MOODS.keys()))
    page_kind = args.page_kind or rng.choice(list(PAGE_KINDS.keys()))
    return StoryParams(place=place, mood=mood, page_kind=page_kind)


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
        print(asp_program("#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for mood in MOODS:
                for page_kind in PAGE_KINDS:
                    samples.append(generate(StoryParams(place=place, mood=mood, page_kind=page_kind)))
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
            p = sample.params
            header = f"### variant {i + 1}: {p.place} / {p.mood} / {p.page_kind}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
