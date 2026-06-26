#!/usr/bin/env python3
"""
storyworlds/worlds/fascinate_happy_ending_lesson_learned_flashback_slice.py
============================================================================

A small slice-of-life storyworld about a child who is fascinated by a little
object, almost makes a mistake, remembers a flashback, and learns a gentle
lesson before the story ends happily.

Premise:
- A child notices something charming in an everyday place.
- The child wants to reach for it right away.
- A parent remembers a past mishap and gives a calm warning.
- The child recalls that flashback, asks first, and helps in a safe way.
- The ending proves the child learned something.

This world is intentionally narrow and constraint-checked: only story variants
that make the "ask first" lesson honest are generated.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "neighbor"


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

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


SETTINGS = {
    "garden": Setting(place="the garden", detail="The garden was quiet except for bees and a soft breeze."),
    "porch": Setting(place="the porch", detail="The porch had a small chair, a potted plant, and a neat view of the yard."),
    "library_steps": Setting(place="the library steps", detail="The steps were warm from the sun, and the front window held a tiny sparkle."),
}

PRIZES = {
    "wind_chime": Prize(
        label="wind chime",
        phrase="a little silver wind chime",
        type="wind_chime",
        owner_kind="neighbor",
    ),
    "shells": Prize(
        label="shell jar",
        phrase="a jar full of beach shells",
        type="shell_jar",
        owner_kind="neighbor",
    ),
    "bookmark": Prize(
        label="bookmark",
        phrase="a ribbon bookmark with a blue tassel",
        type="bookmark",
        owner_kind="neighbor",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Noah", "Max"]
TRAITS = ["curious", "gentle", "lively", "quiet", "cheerful", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, prize) for place in SETTINGS for prize in PRIZES]


def prize_is_charming(prize: Prize) -> bool:
    return prize.type in {"wind_chime", "shell_jar", "bookmark"}


def can_lead_to_lesson(place: str, prize: Prize) -> bool:
    return place in SETTINGS and prize_is_charming(prize)


def explain_rejection(place: str, prize: str) -> str:
    return (
        f"(No story: {prize} at {place} does not fit this small slice-of-life lesson.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about fascination, a flashback, and a happy lesson."
    )
    ap.add_argument("--place", choices=SETTINGS)
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
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, prize=prize, name=name, gender=gender, parent=parent)


def can_story(params: StoryParams) -> bool:
    return can_lead_to_lesson(params.place, PRIZES[params.prize])


def _do_fascination(world: World, child: Entity, prize: Entity) -> None:
    child.memes["fascination"] = child.memes.get("fascination", 0.0) + 1
    world.say(
        f"{child.id} stopped short, because {child.pronoun('possessive')} eyes had found "
        f"{prize.phrase}."
    )
    world.say(
        f"It was the kind of tiny, ordinary thing that could fascinate a child for a long time."
    )


def _flashback(world: World, child: Entity) -> None:
    child.memes["remembering"] = child.memes.get("remembering", 0.0) + 1
    world.say(
        f"Then {child.id} had a flashback to yesterday, when {child.pronoun()} had reached "
        f"for something that was not {child.pronoun('possessive')} and had made a small mess."
    )
    world.say(
        f"That memory made {child.id} pause, because the old mistake still felt fresh."
    )


def _warning(world: World, parent: Entity, child: Entity, prize: Entity) -> None:
    parent.memes["care"] = parent.memes.get("care", 0.0) + 1
    world.say(
        f"{parent.pronoun().capitalize()} smiled and said, "
        f"\"Let's ask {prize.owner or 'first'} before we touch it.\""
    )
    world.say(
        f"{child.id} liked the gentle tone, even if the answer was not the easy one."
    )


def _lesson(world: World, child: Entity, prize: Entity) -> None:
    child.memes["lesson"] = child.memes.get("lesson", 0.0) + 1
    child.memes["patience"] = child.memes.get("patience", 0.0) + 1
    world.say(
        f"{child.id} took a breath and remembered the lesson: kind hands wait for permission."
    )
    world.say(
        f"So {child.id} asked nicely, and the waiting felt better than grabbing."
    )


def _happy_ending(world: World, child: Entity, parent: Entity, prize: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"The answer was yes. Soon {child.id} was helping in a safe way, and {prize.label} stayed tidy."
    )
    world.say(
        f"{parent.pronoun().capitalize()} and {child.id} left with warm smiles, and the little thing that fascinated {child.id} still shimmered in the same happy place."
    )


def tell(setting: Setting, prize_cfg: Prize, child_name: str, child_gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id=prize_cfg.type,
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner="Neighbor",
        caretaker="Neighbor",
    ))
    neighbor = world.add(Entity(id="Neighbor", kind="character", type="neighbor"))

    world.say(f"{child.id} was in {setting.place}. {setting.detail}")
    world.say(
        f"That was where {child.id} noticed {prize.phrase}, and {child.id} was fascinated right away."
    )
    _do_fascination(world, child, prize)
    world.say(
        f"{child.id} wanted to reach for it, because the little shine and little clink felt irresistible."
    )
    _flashback(world, child)
    _warning(world, parent, child, prize)
    _lesson(world, child, prize)
    world.say(
        f"{neighbor.id} heard the question and came over with a smile."
    )
    _happy_ending(world, child, parent, prize)

    world.facts.update(
        child=child,
        parent=parent,
        neighbor=neighbor,
        prize=prize,
        setting=setting,
        lesson=True,
        flashback=True,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    setting = f["setting"]
    return [
        f'Write a short slice-of-life story for a child named {child.id} who is fascinated by {prize.phrase} at {setting.place}.',
        f"Tell a gentle story with a flashback, a lesson learned, and a happy ending about {child.id} in {setting.place}.",
        f'Write a simple story where someone says "ask first" after {child.id} notices {prize.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Where was {child.id} when {child.id} noticed {prize.phrase}?",
            answer=f"{child.id} was at {setting.place}, where the little {prize.label} was easy to see.",
        ),
        QAItem(
            question=f"Why did {child.id} stop before touching {prize.label}?",
            answer=(
                f"{child.id} remembered a flashback from yesterday and learned that kind hands wait for permission."
            ),
        ),
        QAItem(
            question=f"What happy thing happened after {child.id} asked nicely?",
            answer=(
                f"The answer was yes, and {child.id} got to help in a safe way while {prize.label} stayed tidy."
            ),
        ),
        QAItem(
            question=f"Who reminded {child.id} to ask first?",
            answer=f"{parent.pronoun().capitalize()} did, with a calm smile and a gentle voice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fascinated mean?",
            answer="If someone is fascinated, they are very interested in something and want to keep looking at it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short memory of something that happened before the main part of the story.",
        ),
        QAItem(
            question="Why is it polite to ask before touching someone else's things?",
            answer="Asking first shows respect and helps keep other people's things safe and tidy.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the new understanding the character keeps at the end, often after making a mistake or pausing to think.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Prize) :- setting(Place), prize(Prize).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for prize in PRIZES:
        lines.append(asp.fact("prize", prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PRIZES[params.prize], params.name, params.gender, params.parent)
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


CURATED = [
    StoryParams(place="garden", prize="wind_chime", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="porch", prize="bookmark", name="Leo", gender="boy", parent="father"),
    StoryParams(place="library_steps", prize="shells", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for place, prize in combos:
            print(f"  {place:14} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
