#!/usr/bin/env python3
"""
storyworlds/worlds/oodles_caption_repetition_reconciliation_quest_heartwarming.py
=================================================================================

A small heartwarming storyworld about a child, oodles of ideas, and a quest to
find the right caption.

The seed premise:
---
A child has oodles of drawings, but the best one still needs a caption.
They try many captions, repeat the search, disagree kindly, and finally
reconcile with a warm, shared line that fits the picture.

World model:
---
- Physical state tracks the drawing, the note card, and whether the child has
  enough oodles of time, paper, and comfort to keep trying.
- Emotional state tracks hope, frustration, tenderness, and pride.
- Repetition matters: the child keeps trying captions, but each try changes the
  world a little.
- Reconciliation matters: when ideas clash, a helper can mend the mood and
  merge the ideas into one caption.
- Quest matters: the child wants one perfect caption that makes the drawing
  feel complete.

This script follows the Storyweavers contract:
- standalone stdlib script
- story-state driven prose
- QA sets
- inline ASP twin with a Python reasonableness gate
- --verify checks Python/ASP parity and exercises the generator
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
# Core entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore_off: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the kitchen table"
    cozy: bool = True


@dataclass
class Caption:
    id: str
    style: str
    line: str
    warmth: str
    repetition_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    region: str
    value: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "table": Setting(place="the kitchen table", cozy=True),
    "window": Setting(place="the sunny window seat", cozy=True),
    "porch": Setting(place="the porch step", cozy=True),
}

QUEST_ITEMS = {
    "picture": QuestItem(
        id="picture",
        label="drawing",
        phrase="a bright drawing full of oodles of color",
        region="paper",
        value="pride",
    ),
    "bird": QuestItem(
        id="bird",
        label="bird sketch",
        phrase="a little bird sketch with round cheeks",
        region="paper",
        value="care",
    ),
    "garden": QuestItem(
        id="garden",
        label="garden picture",
        phrase="a garden picture with oodles of flowers",
        region="paper",
        value="joy",
    ),
}

CAPTIONS = {
    "gentle": Caption(
        id="gentle",
        style="gentle",
        line="A little picture with oodles of love",
        warmth="soft and kind",
        repetition_hint="again and again",
        tags={"warm", "repeat"},
    ),
    "bright": Caption(
        id="bright",
        style="bright",
        line="Oodles of color, oodles of cheer",
        warmth="sunny and bright",
        repetition_hint="over and over",
        tags={"warm", "repeat"},
    ),
    "home": Caption(
        id="home",
        style="home",
        line="Home is where the heart makes room",
        warmth="safe and snug",
        repetition_hint="many tries",
        tags={"warm", "reconcile"},
    ),
}

NAMES = ["Mina", "Theo", "Lina", "Pip", "Noa", "June", "Arlo", "Bea"]
HELPER_NAMES = ["Grandma", "Dad", "Mom", "Auntie", "Uncle", "Big Sis"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    item: str
    child_name: str
    child_type: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_needs_caption(item: QuestItem) -> bool:
    return item.region == "paper"


def select_caption(item: QuestItem) -> Optional[Caption]:
    if item.id == "picture":
        return CAPTIONS["gentle"]
    if item.id == "bird":
        return CAPTIONS["home"]
    if item.id == "garden":
        return CAPTIONS["bright"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for item in QUEST_ITEMS:
            if select_caption(QUEST_ITEMS[item]) is not None and item_needs_caption(QUEST_ITEMS[item]):
                combos.append((setting, item))
    return combos


def explain_rejection(item: QuestItem) -> str:
    return f"(No story: the chosen item cannot reasonably support a warm caption quest.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
needs_caption(I) :- quest_item(I), paper_item(I).
compatible(S,I) :- setting(S), needs_caption(I), has_caption(I).
valid(S,I) :- compatible(S,I).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in QUEST_ITEMS.items():
        lines.append(asp.fact("quest_item", iid))
        if item.region == "paper":
            lines.append(asp.fact("paper_item", iid))
    for cid, cap in CAPTIONS.items():
        lines.append(asp.fact("caption", cid))
        lines.append(asp.fact("has_caption", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_story_state(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"hope": 1.0, "frustration": 0.0, "pride": 0.0, "warmth": 1.0},
        memes={"tenderness": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="adult",
        meters={"patience": 1.0, "warmth": 1.0},
        memes={"care": 1.0},
    ))
    item = QUEST_ITEMS[params.item]
    quest = world.add(Entity(
        id=item.id,
        kind="thing",
        type="paper_item",
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        caretaker=helper.id,
        meters={"neatness": 1.0, "completion": 0.0},
        memes={"meaning": 1.0},
    ))
    caption = select_caption(item)
    if caption is None:
        raise StoryError(explain_rejection(item))
    world.facts.update(child=child, helper=helper, item=quest, caption=caption)
    return world


def repeated_try(world: World, child: Entity, item: Entity, caption: Caption) -> None:
    world.say(
        f"{child.id} had oodles of ideas, but none felt just right for the {item.label}."
    )
    child.meters["hope"] += 0.5
    child.meters["frustration"] += 0.5
    world.say(
        f"{child.pronoun().capitalize()} tried the same little caption again: “{caption.line}.”"
    )
    world.say(
        f"It sounded kind, but {child.pronoun('possessive')} heart kept asking for one more try."
    )
    child.meters["frustration"] += 0.5
    child.meters["hope"] += 0.25


def reconcile(world: World, child: Entity, helper: Entity, item: Entity, caption: Caption) -> None:
    helper.meters["patience"] += 0.5
    world.say(
        f"Then {helper.id} sat beside {child.id} and listened to every version with a smile."
    )
    world.say(
        f'"What if we keep the oodles part, and make it sound like home too?" {helper.id} asked.'
    )
    child.meters["frustration"] = max(0.0, child.meters["frustration"] - 1.0)
    child.meters["warmth"] += 1.0
    child.meters["pride"] += 1.0
    child.memes["tenderness"] += 1.0
    helper.memes["care"] += 1.0
    item.meters["completion"] = 1.0
    world.say(
        f"{child.id} nodded, and together they turned the words into a shared caption."
    )
    world.say(f'Their final line was: “{caption.line}.”')
    world.say(
        f"At last, the drawing felt complete, and the room felt a little warmer."
    )


def tell_story(world: World, params: StoryParams) -> World:
    child = world.get(params.child_name)
    helper = world.get(params.helper_name)
    item = world.get(params.item)
    caption = world.facts["caption"]

    world.say(
        f"{child.id} sat at {world.setting.place} with oodles of crayons and a half-finished {item.label}."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted a caption that would make the picture glow."
    )
    world.para()
    repeated_try(world, child, item, caption)
    world.say(
        f"The first try did not settle the picture, so {child.id} tried again and again."
    )
    world.para()
    reconcile(world, child, helper, item, caption)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item = world.facts["item"]
    caption = world.facts["caption"]
    return [
        f"Write a heartwarming story about {child.id} searching for the right caption for a {item.label}.",
        f"Tell a gentle tale in which oodles of tries lead to a kind caption like “{caption.line}.”",
        f"Write a story about repetition, reconciliation, and a child who wants one perfect caption.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    caption = world.facts["caption"]
    return [
        QAItem(
            question=f"What was {child.id} trying to make for the {item.label}?",
            answer=f"{child.id} was trying to make a good caption for the {item.label}.",
        ),
        QAItem(
            question=f"Why did {child.id} keep trying captions again and again?",
            answer=f"{child.id} kept trying because the first ideas did not feel just right, so {child.pronoun()} wanted a caption that truly fit the picture.",
        ),
        QAItem(
            question=f"Who helped {child.id} reconcile the different ideas?",
            answer=f"{helper.id} helped by listening kindly and suggesting a way to keep the oodles feeling while making the words warmer.",
        ),
        QAItem(
            question=f"What was the final caption?",
            answer=f'The final caption was “{caption.line}.”',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are oodles?",
            answer="Oodles means a very large amount, like lots and lots of crayons or ideas.",
        ),
        QAItem(
            question="What is a caption?",
            answer="A caption is a short line of words that goes with a picture to explain it or give it a feeling.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement and finding a way to agree kindly.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special search for something important, like the right caption in this story.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="table", item="picture", child_name="Mina", child_type="girl", helper_name="Mom"),
    StoryParams(setting="window", item="bird", child_name="Theo", child_type="boy", helper_name="Grandma"),
    StoryParams(setting="porch", item="garden", child_name="Lina", child_type="girl", helper_name="Dad"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest for the right caption.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[:4] if gender == "girl" else NAMES[2:])
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, item=item, child_name=name, child_type=gender, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_story_state(params)
    tell_story(world, params)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
