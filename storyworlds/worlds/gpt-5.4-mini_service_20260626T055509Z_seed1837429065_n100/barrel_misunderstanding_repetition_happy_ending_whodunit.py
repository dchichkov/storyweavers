#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a barrel, a misunderstanding, and a
happy ending.

A child notices a barrel in the shed, a missing jar of jam, and a trail of clues.
The first clue is misunderstood, then repeated in a steadier way, and the truth
comes out in a gentle, child-facing reveal.

The world is intentionally tiny:
- one detective child
- one helpful grown-up
- one barrel
- one missing object
- a handful of clue variants

The core tension:
- the detective thinks the barrel is hiding the missing object
- repeated clues show that the barrel is innocent
- the actual culprit is not a villain, only a misunderstanding about where the
  jar was put
- the ending is warm, tidy, and satisfying
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str
    setting_detail: str


@dataclass
class Clue:
    id: str
    line: str
    meaning: str
    kind: str  # "true", "misleading", "repeat"


@dataclass
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    barrel_label: str = "barrel"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clues_seen: list[str] = []

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
    "shed": Setting(place="the old shed", setting_detail="Dusty shelves leaned against the wall, and a barrel sat in the corner."),
    "kitchen": Setting(place="the kitchen", setting_detail="The counters were clean and bright, and a little barrel of apples stood nearby."),
    "cellar": Setting(place="the cellar", setting_detail="The cellar was cool and dim, with a barrel under the stairs."),
}

MYSTERIES = {
    "jam": Mystery(id="jam", missing_label="jam jar", missing_phrase="a small jar of strawberry jam"),
    "cookie_tin": Mystery(id="cookie_tin", missing_label="cookie tin", missing_phrase="a round tin of sugar cookies"),
    "button_box": Mystery(id="button_box", missing_label="button box", missing_phrase="a tin box full of buttons"),
}

CLUES = {
    "scratch": Clue(
        id="scratch",
        line="A scratch mark ran down the side of the barrel.",
        meaning="The mark looked scary, but it only showed that the barrel had been rolled before.",
        kind="misleading",
    ),
    "lid": Clue(
        id="lid",
        line="The lid on the barrel was shut tight.",
        meaning="The tight lid meant nothing had simply fallen out of the barrel.",
        kind="true",
    ),
    "label": Clue(
        id="label",
        line="A little paper label on the barrel was peeling at one corner.",
        meaning="The label named the barrel's old use, not the missing thing.",
        kind="misleading",
    ),
    "footprints": Clue(
        id="footprints",
        line="Tiny footprints led past the barrel and toward the pantry shelf.",
        meaning="The trail pointed away from the barrel and toward the real place.",
        kind="true",
    ),
    "repeat_footprints": Clue(
        id="repeat_footprints",
        line="The tiny footprints still pointed past the barrel and toward the pantry shelf.",
        meaning="The clue was repeated to make the path clearer.",
        kind="repeat",
    ),
    "repeat_lid": Clue(
        id="repeat_lid",
        line="The lid was still shut tight on the barrel.",
        meaning="The repeated clue kept the detective from blaming the barrel too fast.",
        kind="repeat",
    ),
}

GROWN_UP_NAMES = ["Mira", "Ben", "Tara", "Jon"]
CHILD_NAMES = ["Pip", "Nia", "Leo", "Mina", "Zed"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    child_name: str
    child_type: str = "boy"
    grown_up_name: str = "Mira"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit storyworld with a barrel, a misunderstanding, repetition, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grown-up")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    child_type = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    grown = args.grown_up or rng.choice(GROWN_UP_NAMES)
    return StoryParams(setting=setting, mystery=mystery, child_name=name, child_type=child_type, grown_up_name=grown)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, grown: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} was a curious little {child.type} who loved solving small mysteries."
    )
    world.say(
        f"That morning, {child.id} noticed that {mystery.missing_phrase} was gone, and {grown.id} said they should look in {world.setting.place}."
    )


def inspect_barrel(world: World, child: Entity, barrel: Entity, clue: Clue) -> None:
    child.memes["suspicion"] = child.memes.get("suspicion", 0) + 1
    world.say(
        f"{child.id} peered at the barrel. {clue.line}"
    )


def repeat_clue(world: World, child: Entity, clue: Clue) -> None:
    world.clues_seen.append(clue.id)
    world.say(clue.line)


def reveal_truth(world: World, child: Entity, grown: Entity, mystery: Mystery, barrel: Entity) -> None:
    child.memes["understanding"] = 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"Then {grown.id} pointed to the pantry shelf and laughed softly. "
        f"The missing {mystery.missing_label} had been moved there earlier and forgotten."
    )
    world.say(
        f"The barrel had not taken anything at all. It was only standing there with its lid shut, looking blamed for no reason."
    )
    world.say(
        f"{child.id} smiled, apologized to the barrel in a whisper, and carried the {mystery.missing_label} back to the table."
    )
    world.say(
        f"By the end, the barrel was just a barrel again, the mystery was solved, and {child.id} and {grown.id} shared jam or cookies or buttons with a happy grin."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    grown = world.add(Entity(id=params.grown_up_name, kind="character", type="woman" if params.grown_up_name in {"Mira", "Tara"} else "man"))
    mystery = MYSTERIES[params.mystery]
    barrel = world.add(Entity(id="barrel", kind="thing", label="barrel", type="barrel"))

    world.facts.update(child=child, grown=grown, mystery=mystery, barrel=barrel)

    introduce(world, child, grown, mystery)
    world.para()

    world.say(world.setting.setting_detail)
    inspect_barrel(world, child, barrel, CLUES["scratch"])
    repeat_clue(world, child, CLUES["repeat_lid"])
    repeat_clue(world, child, CLUES["footprints"])
    world.para()

    world.say(
        f"{child.id} first thought the barrel was hiding the missing thing, because the scratch mark looked like a secret."
    )
    world.say(
        f"But the repeated clues were steadier: the lid was shut, and the footprints kept leading away from the barrel."
    )
    reveal_truth(world, child, grown, mystery, barrel)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    grown: Entity = f["grown"]
    return [
        f'Write a gentle whodunit for a young child featuring a {mystery.barrel_label} and a lost {mystery.missing_label}.',
        f"Tell a story where {child.id} makes a misunderstanding about the barrel, then notices the clue again and again until the truth is clear.",
        f"Write a short mystery with repetition, a barrel, and a happy ending where {grown.id} helps solve the puzzle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    grown: Entity = f["grown"]
    mystery: Mystery = f["mystery"]
    qa = [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {mystery.missing_phrase}.",
        ),
        QAItem(
            question=f"What did {child.id} first misunderstand about the barrel?",
            answer=f"{child.id} first thought the barrel was hiding the missing {mystery.missing_label}, but that was not true.",
        ),
        QAItem(
            question=f"What repeated clue helped {child.id} stop blaming the barrel?",
            answer="The repeated clues were that the lid was shut tight and the tiny footprints led past the barrel toward the pantry shelf.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{grown.id} helped by pointing to the pantry shelf and explaining where the missing thing had really been moved.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the barrel innocent, the missing {mystery.missing_label} recovered, and everyone smiling.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question="What is a barrel?",
            answer="A barrel is a large round container, often made of wood or metal, that can hold food, water, or other things.",
        ),
        QAItem(
            question="Why can a clue be misunderstood?",
            answer="A clue can be misunderstood when it looks important but does not mean what it first seems to mean.",
        ),
        QAItem(
            question="Why do stories repeat clues in mysteries?",
            answer="Stories repeat clues so the important parts stand out and the reader can follow the answer more easily.",
        ),
        QAItem(
            question=f"What kind of missing thing was in this story?",
            answer=f"It was {mystery.missing_phrase}, which is something small and ordinary that can be moved and forgotten.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
barrel(barrel).
setting(shed). setting(kitchen). setting(cellar).

missing(jam).
missing(cookie_tin).
missing(button_box).

misleading(scratch).
misleading(label).
true_clue(lid).
true_clue(footprints).

repeated(lid).
repeated(footprints).

mystery_ok(S, M) :- setting(S), missing(M).
has_misunderstanding(M) :- missing(M).
happy_ending(M) :- missing(M), true_clue(lid), true_clue(footprints).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("missing", m))
    for c in CLUES.values():
        if c.kind == "misleading":
            lines.append(asp.fact("misleading", c.id))
        elif c.kind == "true":
            lines.append(asp.fact("true_clue", c.id))
        else:
            lines.append(asp.fact("repeated", c.id))
    lines.append(asp.fact("barrel", "barrel"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    atoms = sorted(set(asp.atoms(model, "happy_ending")))
    if atoms:
        print("OK: ASP rules can derive a happy ending.")
        return 0
    print("MISMATCH: ASP rules failed to derive happy_ending/1.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(setting="shed", mystery="jam", child_name="Pip", child_type="boy", grown_up_name="Mira"),
            StoryParams(setting="kitchen", mystery="cookie_tin", child_name="Nia", child_type="girl", grown_up_name="Ben"),
            StoryParams(setting="cellar", mystery="button_box", child_name="Leo", child_type="boy", grown_up_name="Tara"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen = set()
        for i in range(max(args.n, 1)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.child_name} / {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
