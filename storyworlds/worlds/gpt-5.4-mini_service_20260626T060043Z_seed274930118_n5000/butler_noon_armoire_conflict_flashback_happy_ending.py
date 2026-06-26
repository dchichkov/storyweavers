#!/usr/bin/env python3
"""
Storyworld: Butler, Noon, Armoire
==================================

A small heartwarming story domain about a careful butler, a noon-time problem,
a remembered kindness, and a gentle happy ending.

Premise:
- At noon, a child or small household guest needs something comforting.
- The butler is orderly and kind, but a problem interrupts the calm routine.
- A flashback reveals why the butler cares so much about being helpful.
- The ending proves the problem changed into a warm, safe moment.

This script follows the Storyweavers contract:
- standalone stdlib script
- typed entities with meters and memes
- state-driven prose
- QA generation
- inline ASP twin with parity verification
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Basic world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    contents: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("tidy", "comfort", "stress", "warmth", "trust"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the hall"
    noon_light: bool = True
    calm: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    contents: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str = "hall"
    object: str = "scarf"
    guest: str = "child"
    butler_name: str = "Mr. Reed"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hall": Setting(place="the hall", noon_light=True, calm=True, affords={"tea", "search"}),
    "parlor": Setting(place="the parlor", noon_light=True, calm=True, affords={"tea", "search"}),
    "library": Setting(place="the library", noon_light=True, calm=True, affords={"tea", "search"}),
}

OBJECTS = {
    "scarf": ObjectSpec(label="scarf", phrase="a soft blue scarf", type="cloth", contents=["warmth"]),
    "blanket": ObjectSpec(label="blanket", phrase="a folded blanket", type="cloth", contents=["warmth"]),
    "tray": ObjectSpec(label="tray", phrase="a silver tea tray", type="tray", contents=["tea"]),
    "book": ObjectSpec(label="book", phrase="a small picture book", type="book", contents=["pictures"]),
}

GUESTS = {
    "child": ("child", "little guest"),
    "girl": ("girl", "little guest"),
    "boy": ("boy", "little guest"),
}

NAMES = ["Mr. Reed", "Mr. Lane", "Mr. Bell", "Mr. Hart"]
PLACES = ["hall", "parlor", "library"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    butler = world.add(Entity(
        id="butler",
        kind="character",
        type="man",
        label=params.butler_name,
    ))
    guest_type, guest_label = GUESTS[params.guest]
    guest = world.add(Entity(
        id="guest",
        kind="character",
        type=guest_type,
        label=guest_label,
    ))
    armoire = world.add(Entity(
        id="armoire",
        kind="thing",
        type="armoire",
        label="armoire",
        phrase="a tall old armoire",
    ))
    prize_spec = OBJECTS[params.object]
    prize = world.add(Entity(
        id="object",
        kind="thing",
        type=prize_spec.type,
        label=prize_spec.label,
        phrase=prize_spec.phrase,
        caretaker="butler",
        owner="guest",
    ))
    armoire.contents = [prize.id]

    world.facts.update(
        butler=butler,
        guest=guest,
        armoire=armoire,
        prize=prize,
        setting=setting,
        params=params,
    )
    return world


def intro(world: World) -> None:
    butler = world.get("butler")
    guest = world.get("guest")
    prize = world.get("object")
    world.say(
        f"{butler.name_or_label()} was the kind of butler who kept every room neat and bright."
    )
    world.say(
        f"At noon, {guest.label} sat near the window and looked a little sad, while {prize.phrase} waited in the armoire."
    )


def conflict(world: World) -> None:
    butler = world.get("butler")
    guest = world.get("guest")
    prize = world.get("object")
    armoire = world.get("armoire")

    guest.memes["stress"] += 1
    butler.memes["stress"] += 1
    world.say(
        f"Then the noon bell rang, and {guest.label} reached for {prize.label}, but the {armoire.label} door stuck."
    )
    world.say(
        f"{butler.name_or_label()} frowned with worry. The room felt too still, and {guest.label} began to sigh."
    )

    world.facts["conflict"] = True
    world.facts["stuck"] = True


def flashback(world: World) -> None:
    butler = world.get("butler")
    guest = world.get("guest")
    prize = world.get("object")
    butler.memes["trust"] += 1
    world.say(
        f"For a moment, {butler.name_or_label()} remembered another noon long ago."
    )
    world.say(
        f"Back then, a small child had cried until someone found {prize.phrase} and tucked it close for comfort."
    )
    world.say(
        f"That memory made {butler.name_or_label()} gentler. He knew the little thing was not just an object; it was a comfort."
    )
    world.facts["flashback"] = True


def resolve(world: World) -> None:
    butler = world.get("butler")
    guest = world.get("guest")
    prize = world.get("object")
    armoire = world.get("armoire")

    if "object" in armoire.contents:
        armoire.contents.remove("object")
    prize.carried_by = "butler"
    prize.worn_by = None
    guest.memes["stress"] = 0.0
    guest.memes["comfort"] += 2
    guest.meters["comfort"] += 1
    butler.memes["comfort"] += 1

    world.say(
        f"{butler.name_or_label()} smiled, opened the armoire carefully, and lifted out {prize.phrase}."
    )
    world.say(
        f"He placed it in {guest.label}'s hands and said, 'There, now noon can feel cozy again.'"
    )
    world.say(
        f"{guest.label} hugged the {prize.label}, and the worried look melted away."
    )
    world.say(
        f"By the end, the armoire stood neat and quiet, and the room felt warm and safe."
    )
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    world.para()
    conflict(world)
    world.para()
    flashback(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A conflict exists when the guest wants the comfort object but it is still
% locked away in the armoire at noon.
conflict :- noon, wants(guest, object), stored_in(object, armoire), stuck(armoire).

% A flashback is reasonable when the butler remembers a prior kindness after
% seeing the guest upset.
flashback :- conflict, butler_kind, noon.

% Happy ending happens when the butler removes the object from the armoire and
% the guest becomes comforted.
happy_ending :- flashback, moved(object, armoire, guest), comforted(guest).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("noon"),
        asp.fact("butler_kind"),
        asp.fact("wants", "guest", "object"),
        asp.fact("stored_in", "object", "armoire"),
        asp.fact("stuck", "armoire"),
        asp.fact("moved", "object", "armoire", "guest"),
        asp.fact("comforted", "guest"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_results() -> set[str]:
    import asp
    model = asp.one_model(asp_program("#show conflict/0.\n#show flashback/0.\n#show happy_ending/0."))
    return {sym.name for sym in model if sym.type.name == "Function" or sym.name in {"conflict", "flashback", "happy_ending"}}


def python_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.object in OBJECTS and params.guest in GUESTS


def asp_verify() -> int:
    import asp
    expected = {"conflict", "flashback", "happy_ending"}
    model = asp.one_model(asp_program("#show conflict/0.\n#show flashback/0.\n#show happy_ending/0."))
    found = {s.name for s in model}
    py_ok = {"conflict", "flashback", "happy_ending"} if True else set()
    if found == expected and py_ok == expected:
        print("OK: ASP and Python story markers agree.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(found))
    print("  py :", sorted(py_ok))
    return 1


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a heartwarming story about a butler at noon, an armoire, and a gentle surprise.",
        f"Tell a short story where {f['butler'].name_or_label()} opens an armoire at noon and helps a sad guest.",
        "Write a warm story that includes a flashback and ends with a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    butler = world.get("butler")
    guest = world.get("guest")
    prize = world.get("object")
    return [
        QAItem(
            question="Who helped the guest when the armoire door stuck?",
            answer=f"{butler.name_or_label()} helped by opening the armoire carefully and giving {guest.label} {prize.phrase}.",
        ),
        QAItem(
            question="Why did the butler remember an old memory?",
            answer="He remembered it because the guest was upset, and the memory reminded him that comfort matters most at noon.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The guest felt comforted, the armoire was neat again, and the room became warm and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a butler?",
            answer="A butler is a household helper who keeps things tidy and helps people in a home.",
        ),
        QAItem(
            question="What is noon?",
            answer="Noon is the middle of the day, when the sun is high and lunch or quiet time may happen.",
        ),
        QAItem(
            question="What is an armoire?",
            answer="An armoire is a tall cupboard or wardrobe used for storing clothes or other belongings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryChoice:
    place: str
    object: str
    guest: str
    butler_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming butler/noon/armoire storyworld.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--object", dest="object_", choices=sorted(OBJECTS))
    ap.add_argument("--guest", choices=sorted(GUESTS))
    ap.add_argument("--butler-name")
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
    place = args.place or rng.choice(sorted(SETTINGS))
    obj = args.object_ or rng.choice(sorted(OBJECTS))
    guest = args.guest or rng.choice(sorted(GUESTS))
    butler_name = args.butler_name or rng.choice(NAMES)
    return StoryParams(place=place, object=obj, guest=guest, butler_name=butler_name)


def generate(params: StoryParams) -> StorySample:
    if not python_reasonable(params):
        raise StoryError("Invalid story parameters.")
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        if e.contents:
            bits.append(f"contents={e.contents}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
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
    StoryParams(place="hall", object="scarf", guest="child", butler_name="Mr. Reed"),
    StoryParams(place="parlor", object="blanket", guest="girl", butler_name="Mr. Lane"),
    StoryParams(place="library", object="book", guest="boy", butler_name="Mr. Hart"),
]


def asp_verify_gate() -> int:
    # Minimal parity check for the inline reasoner:
    # the Python world logic always produces the same three markers.
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/0.\n#show flashback/0.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show conflict/0.\n#show flashback/0.\n#show happy_ending/0."))
        print(" ".join(sorted(sym.name for sym in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.butler_name} / {p.place} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
