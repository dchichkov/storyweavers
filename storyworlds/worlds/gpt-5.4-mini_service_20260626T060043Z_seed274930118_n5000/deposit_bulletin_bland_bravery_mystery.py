#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/deposit_bulletin_bland_bravery_mystery.py
===============================================================================================================

A small mystery-flavored storyworld about a child, a bulletin, a deposit, and
a brave choice.

Premise:
- A child notices a strange bulletin in a quiet place.
- The bulletin is oddly bland, which makes it feel even more suspicious.
- A hidden deposit slot or envelope can be used to return the right clue.

Turn:
- The child must choose whether to be brave and make the deposit.
- The bulletin's message only makes sense after the brave action.

Resolution:
- The deposit unlocks the missing clue.
- The child learns the plain, bland message was not boring at all; it was
  a careful cover for a mystery.

The world is intentionally tiny and constraint-checked. It models physical
state with meters and emotional state with memes, and it includes an inline
ASP twin for parity verification.
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

# Keep the world small and deterministic once params are chosen.
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    opened: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    shadows: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_in: str
    reveals: str
    is_deposit: bool = False


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTINGS: dict[str, Setting] = {
    "library": Setting(
        place="the old library",
        mood="quiet",
        shadows=True,
        affordances={"bulletin", "deposit"},
    ),
    "station": Setting(
        place="the train station",
        mood="echoing",
        shadows=True,
        affordances={"bulletin", "deposit"},
    ),
    "lobby": Setting(
        place="the museum lobby",
        mood="still",
        shadows=False,
        affordances={"bulletin", "deposit"},
    ),
}

CLUES: dict[str, Clue] = {
    "key": Clue(
        id="key",
        label="brass key",
        phrase="a small brass key",
        hidden_in="pocket",
        reveals="a hidden drawer",
        is_deposit=True,
    ),
    "ticket": Clue(
        id="ticket",
        label="paper ticket",
        phrase="a paper ticket with a blue stripe",
        hidden_in="book",
        reveals="a late notice",
        is_deposit=True,
    ),
    "token": Clue(
        id="token",
        label="tin token",
        phrase="a round tin token",
        hidden_in="bench",
        reveals="a locker number",
        is_deposit=True,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lena", "Ivy", "June", "Tess"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Milo", "Theo", "Jack"]
TRAITS = ["curious", "gentle", "shy", "careful", "spirited"]

KNOWLEDGE = {
    "deposit": [
        (
            "What is a deposit?",
            "A deposit is something you put down or hand in for safekeeping, or to show you have returned it to the right place.",
        )
    ],
    "bulletin": [
        (
            "What is a bulletin?",
            "A bulletin is a short public notice that shares news, instructions, or a message for many people to read.",
        )
    ],
    "bland": [
        (
            "What does bland mean?",
            "If something is bland, it is plain and not strong in flavor or style.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is when someone does something scary or hard because it needs to be done.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that needs clues to help explain it.",
        )
    ],
}


ASP_RULES = r"""
% A clue is available when the setting supports both the bulletin and the deposit action.
available(S, C) :- setting(S), clue(C), affords(S, bulletin), affords(S, deposit).

% The story is valid when the clue is deposit-worthy and the setting can host it.
valid_story(S, C) :- available(S, C), deposit_worthy(C).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.shadows:
            lines.append(asp.fact("shadows", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("deposit_worthy", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return sorted((sid, cid) for sid in SETTINGS for cid in CLUES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a bulletin and a brave deposit.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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
    if args.setting and args.clue:
        pass
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.name is None:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    else:
        name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, parent=parent)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    clue_def = CLUES[params.clue]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    board = world.add(Entity(id="bulletin", kind="thing", type="bulletin", label="bulletin board", phrase="a bulletin board with a pinned note"))
    deposit_box = world.add(Entity(id="deposit_box", kind="thing", type="box", label="deposit slot", phrase="a narrow deposit slot"))
    clue = world.add(Entity(
        id=clue_def.id,
        kind="thing",
        type=clue_def.id,
        label=clue_def.label,
        phrase=clue_def.phrase,
        hidden_in=clue_def.hidden_in,
    ))

    hero.memes["curiosity"] = 1.0
    hero.memes["bravery"] = 0.0
    clue.meters["found"] = 0.0
    clue.meters["deposited"] = 0.0

    world.facts = {
        "hero": hero,
        "parent": parent,
        "board": board,
        "deposit_box": deposit_box,
        "clue": clue,
        "clue_def": clue_def,
        "setting": setting,
    }
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    clue: Entity = f["clue"]
    clue_def: Clue = f["clue_def"]
    setting: Setting = f["setting"]

    world.say(f"{hero.id} came to {setting.place}, where the air felt {setting.mood} and a bulletin board waited by the wall.")
    world.say(f"On the board was a bland little notice, plain as paper and neat as a folded square. That made {hero.id} wonder why it felt so strange.")

    world.para()
    world.say(f"Near the notice, {hero.id} found {clue_def.phrase}.")
    world.say(f"It looked like the kind of thing that belonged in a mystery, not in a pocket or under a bench.")
    world.say(f"{hero.id} wanted to ask {parent.label} right away, but the quiet place seemed to hold its breath.")

    world.para()
    hero.memes["fear"] = 1.0
    world.say(f"Then {hero.id} noticed a tiny deposit slot under the bulletin board.")
    world.say(f'The plain notice said, "If you found the right thing, make a deposit here."')
    world.say(f"{hero.id} felt a small wobble of fear, because the hallway behind the board was dark and still.")

    hero.memes["bravery"] = 1.0
    clue.meters["deposited"] = 1.0
    clue.carried_by = None
    world.say(f"But {hero.id} was brave. {hero.id} slid the {clue.label} into the deposit slot.")
    world.say(f"The bulletin clicked, and a hidden drawer opened at once.")

    world.para()
    clue.meters["found"] = 1.0
    clue.hidden_in = None
    world.say(f"Inside was the missing answer: {clue_def.reveals}.")
    world.say(f"{hero.id} smiled as {parent.label} came closer, and the bland little bulletin did not look boring anymore.")
    world.say(f"It had been a careful clue all along, and bravery had helped turn the mystery into a solved one.")


def render_story(params: StoryParams) -> World:
    world = make_world(params)
    narrate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue_def: Clue = f["clue_def"]
    setting: Setting = f["setting"]
    return [
        f'Write a short mystery story for a young child about {hero.id}, a bulletin board, and a brave deposit at {setting.place}.',
        f"Tell a gentle story where a child finds {clue_def.phrase}, notices a bland bulletin, and makes a brave deposit.",
        f'Write a child-friendly mystery that uses the words "deposit", "bulletin", and "bland" and ends with bravery solving the puzzle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    clue_def: Clue = f["clue_def"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the mystery clue?",
            answer=f"{hero.id} found {clue_def.phrase} at {setting.place}, near the bulletin board.",
        ),
        QAItem(
            question="Why did the bulletin seem strange?",
            answer="It was a bland, plain notice, which made it feel suspicious and mysterious instead of ordinary.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do with the {clue_def.label}?",
            answer=f"{hero.id} made a deposit by sliding the {clue_def.label} into the slot under the bulletin board.",
        ),
        QAItem(
            question=f"What happened after {hero.id} made the deposit?",
            answer=f"A hidden drawer opened, and the missing answer was found. Then {parent.label} could see that the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["deposit", "bulletin", "bland", "bravery", "mystery"]:
        q, a = KNOWLEDGE[key][0]
        out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.hidden_in is not None:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by is not None:
            bits.append(f"carried_by={e.carried_by}")
        if e.opened:
            bits.append("opened=True")
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = render_story(params)
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


def explain_rejection() -> str:
    return "(No story: the requested choices do not make a valid mystery.)"


CURATED = [
    StoryParams(setting="library", clue="key", name="Mia", gender="girl", parent="mother"),
    StoryParams(setting="station", clue="ticket", name="Finn", gender="boy", parent="father"),
    StoryParams(setting="lobby", clue="token", name="Lena", gender="girl", parent="mother"),
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
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible story combos:")
        for s, c in pairs:
            print(f"  {s:10} {c}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
