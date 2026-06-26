#!/usr/bin/env python3
"""
Story world: a tiny ghost story about a dresser, the woods, suspense, rhyme,
and a happy ending.

The premise is simple: a child hears strange bumps near an old dresser by the
woods. The bumps feel spooky at first, but the world model shows they come from
a harmless helper, not a danger. Suspense rises, the child investigates, and the
ending proves the change: fear turns into comfort, and the woods stop seeming
so dark.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

@dataclass
class Setting:
    place: str
    outdoors: bool = True
    woods_edge: bool = True


@dataclass
class Haunting:
    name: str
    sound: str
    motion: str
    fear_word: str
    reveal: str
    rhyme_a: str
    rhyme_b: str


SETTINGS = {
    "woods": Setting(place="the woods", outdoors=True, woods_edge=True),
    "house": Setting(place="the little house by the woods", outdoors=False, woods_edge=True),
}

HAUNTINGS = {
    "bump": Haunting(
        name="bump",
        sound="bump-bump",
        motion="a little tapping from the dresser drawer",
        fear_word="spooky",
        reveal="a sleepy raccoon had been nudging the drawer with its paws",
        rhyme_a="dark and stark",
        rhyme_b="spark and park",
    ),
    "creak": Haunting(
        name="creak",
        sound="creak-creak",
        motion="a slow creak from the old dresser door",
        fear_word="eerie",
        reveal="the wind had been rocking a loose drawer, back and forth",
        rhyme_a="moon and tune",
        rhyme_b="soon and spoon",
    ),
    "rustle": Haunting(
        name="rustle",
        sound="rustle-rustle",
        motion="a tiny rustle near the woods path",
        fear_word="shivery",
        reveal="a hedgehog was shuffling leaves into a cozy nest",
        rhyme_a="trees and breeze",
        rhyme_b="keys and ease",
    ),
}

OBJECTS = {
    "dresser": {
        "label": "old dresser",
        "phrase": "an old dresser with a round mirror",
        "location": "the bedroom window",
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a small lantern with a warm gold glow",
        "location": "the bedside table",
    },
    "blanket": {
        "label": "blanket",
        "phrase": "a soft blanket with blue stars",
        "location": "the chair",
    },
}

GHOSTLY_WORDS = ["spooky", "shadowy", "whispery", "mysterious", "shivery"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    haunting: str
    object: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for haunt_id, haunt in HAUNTINGS.items():
            for obj_id in OBJECTS:
                if setting.woods_edge and obj_id == "dresser":
                    combos.append((setting_id, haunt_id, obj_id))
    return combos


def explain_rejection(setting_id: str, haunt_id: str, obj_id: str) -> str:
    return (
        f"(No story: the chosen set doesn't fit the ghost-story premise. "
        f"Try a dresser, the woods, and a haunting that can be noticed near the house.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.haunting or args.object:
        filtered = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.haunting is None or c[1] == args.haunting)
            and (args.object is None or c[2] == args.object)
        ]
        if not filtered:
            raise StoryError("(No valid combination matches the given options.)")
    else:
        filtered = combos

    setting_id, haunt_id, obj_id = rng.choice(sorted(filtered))
    name = args.name or rng.choice(["Mina", "Theo", "Lena", "Owen", "Ruby", "Iris"])
    return StoryParams(setting=setting_id, haunting=haunt_id, object=obj_id, name=name)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def rhyme_line(h: Haunting) -> str:
    return f"{h.rhyme_a} / {h.rhyme_b}"


def generate_story(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    haunting = HAUNTINGS[params.haunting]
    obj_cfg = OBJECTS[params.object]

    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    dresser = world.add(Entity(
        id="dresser", kind="thing", type="dresser", label=obj_cfg["label"],
        phrase=obj_cfg["phrase"], location=obj_cfg["location"], caretaker=child.id
    ))
    lantern = world.add(Entity(
        id="lantern", kind="thing", type="lantern", label="lantern",
        phrase=OBJECTS["lantern"]["phrase"], location="the bedside table"
    ))

    world.facts.update(child=child, dresser=dresser, lantern=lantern, setting=setting, haunting=haunting)

    # Act 1
    world.say(
        f"{child.id} lived in a little house by {setting.place} and loved "
        f"{dresser.phrase} even when the night looked dark."
    )
    world.say(
        f"One evening, the child heard {haunting.sound} near the dresser, "
        f"and the sound felt {haunting.fear_word}."
    )
    world.say(
        f"The room grew still. Even the lantern seemed to hold its breath."
    )

    # Act 2
    world.para()
    child.memes["fear"] = 1.0
    child.memes["suspense"] = 1.0
    world.say(
        f"{child.id} tiptoed closer. {haunting.motion} made the floor feel "
        f"cold, and the woods outside whispered with the wind."
    )
    world.say(
        f'"Is it a ghost?" {child.id} asked. The question hung in the air like a little bell.'
    )
    world.say(
        f"From the woods came another {haunting.sound}, and the child shivered."
    )

    # Turn / reveal
    child.memes["courage"] = 1.0
    world.para()
    world.say(
        f"{child.id} lifted the lantern and opened the dresser door. There was no ghost at all."
    )
    world.say(
        f"Instead, {haunting.reveal}. That was why the sound kept coming back."
    )
    world.say(
        f"The scary noise had a sleepy reason, and the reason was small enough to fit in one honest look."
    )

    # Ending image
    child.memes["fear"] = 0.0
    child.memes["joy"] = 1.0
    child.memes["relief"] = 1.0
    world.para()
    world.say(
        f"{child.id} laughed, and the laugh sounded brighter than the dark. "
        f"The woods no longer felt so spooky."
    )
    world.say(
        f'That night, {child.id} said, "{rhyme_line(haunting)}," and tucked the blanket up to the chin.'
    )
    world.say(
        f"The dresser stood quietly by the window, the lantern glowed like a tiny moon, "
        f"and the happy ending settled over the house as softly as a blanket."
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    haunting: Haunting = f["haunting"]
    return [
        f'Write a short ghost story for a young child that includes "{child.id}" and the woods.',
        f"Tell a suspenseful but gentle story about a dresser, a strange sound, and a happy ending.",
        f'Write a child-friendly rhyme-filled story where "{haunting.sound}" turns out not to be a ghost.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    haunting: Haunting = f["haunting"]
    setting: Setting = f["setting"]
    dresser: Entity = f["dresser"]
    qa = [
        QAItem(
            question=f"What made {child.id} feel scared near the dresser?",
            answer=(
                f"{haunting.sound} made {child.id} feel scared because it sounded spooky in the quiet house by {setting.place}."
            ),
        ),
        QAItem(
            question=f"What was the strange sound really coming from?",
            answer=(
                f"It was not a ghost. The sound came from a real, harmless cause near the dresser, so the mystery had a safe answer."
            ),
        ),
        QAItem(
            question=f"What was the dresser like in the story?",
            answer=(
                f"It was {dresser.phrase}, and it stood quietly by the window while the child looked for the source of the sound."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    haunting: Haunting = f["haunting"]
    out = [
        QAItem(
            question="What is a dresser?",
            answer="A dresser is a piece of furniture with drawers that people use to store clothes."
        ),
        QAItem(
            question="What are the woods?",
            answer="The woods are a place with many trees, leaves, and often quiet shadows at night."
        ),
        QAItem(
            question="Why can a story have suspense?",
            answer="A story has suspense when something seems uncertain or spooky for a little while, so you want to know what happens next."
        ),
        QAItem(
            question="What makes a rhyme?",
            answer="A rhyme is made when words sound alike at the end, like tune and moon."
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the ending feels safe, kind, or joyful."
        ),
        QAItem(
            question=f'Why do "{haunting.sound}" sounds feel spooky?',
            answer="A sudden sound can feel spooky in the dark because people do not know right away what caused it."
        ),
    ]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(S, H, O) :- setting(S), haunting(H), object(O), woods_edge(S), O = dresser.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.woods_edge:
            lines.append(asp.fact("woods_edge", sid))
    for hid, _ in HAUNTINGS.items():
        lines.append(asp.fact("haunting", hid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = World(place=SETTINGS[params.setting].place)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="woods", haunting="bump", object="dresser", name="Mina"),
    StoryParams(setting="house", haunting="creak", object="dresser", name="Theo"),
    StoryParams(setting="woods", haunting="rustle", object="dresser", name="Ruby"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: dresser, woods, suspense, rhyme, happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunting", choices=HAUNTINGS)
    ap.add_argument("--object", choices=OBJECTS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.haunting} at {p.setting} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
