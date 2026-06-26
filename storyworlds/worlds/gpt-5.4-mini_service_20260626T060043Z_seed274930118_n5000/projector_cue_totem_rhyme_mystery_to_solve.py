#!/usr/bin/env python3
"""
A standalone storyworld for a rhyming mystery tale.

Domain sketch:
- A child in a small show-space wants to use a projector.
- A lost cue and a carved totem create a mystery to solve.
- A little magic helps reveal the answer.
- The story should read like a complete rhyming story with a clear turn:
  missing cue -> careful search -> magical reveal -> happy resolution.

The simulation tracks:
- physical meters: where objects are, whether they are hidden, lit, found
- emotional memes: worry, hope, pride, relief, wonder
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little stage room"
    indoor: bool = True
    holds: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    caretaker_type: str
    prop: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "stage": Setting(place="the little stage room", indoor=True, holds={"projector", "cue", "totem", "magic"}),
    "attic": Setting(place="the cozy attic", indoor=True, holds={"projector", "cue", "totem", "magic"}),
}

# The property that can go missing.
PROPS = {
    "projector": {
        "label": "projector",
        "phrase": "a shiny projector",
        "type": "projector",
        "key": "beam",
    },
    "cue": {
        "label": "cue",
        "phrase": "a striped cue stick",
        "type": "cue",
        "key": "tap",
    },
    "totem": {
        "label": "totem",
        "phrase": "a carved wooden totem",
        "type": "totem",
        "key": "glow",
    },
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Zoe", "Ivy"],
    "boy": ["Theo", "Finn", "Leo", "Max", "Ben"],
}
CARETAKERS = {
    "mother": "mother",
    "father": "father",
}
FEELINGS = ["worry", "hope", "wonder", "pride", "relief"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def setup_name(name: str, child_type: str) -> str:
    return f"little {child_type} {name}"


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_type,
            meters={"steps": 0, "search": 0, "found": 0},
            memes={"worry": 0, "hope": 0, "wonder": 0, "pride": 0, "relief": 0},
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=params.caretaker_type,
            label=params.caretaker_type,
            meters={"help": 0},
            memes={"worry": 0, "pride": 0, "relief": 0},
        )
    )
    prop_cfg = PROPS[params.prop]
    prop = world.add(
        Entity(
            id=prop_cfg["type"],
            type=prop_cfg["type"],
            label=prop_cfg["label"],
            phrase=prop_cfg["phrase"],
            owner=child.id,
            caretakers=[caretaker.id],
            meters={"hidden": 1, "lit": 0, "found": 0},
            memes={"mystery": 1},
        )
    )

    world.facts.update(child=child, caretaker=caretaker, prop=prop, params=params)
    return world


def search_for_clue(world: World) -> None:
    child = world.facts["child"]
    prop = world.facts["prop"]
    child.meters["search"] += 1
    child.memes["worry"] += 1
    child.memes["hope"] += 1
    world.say(
        f"{child.id} paced with a chase in a haze, "
        f"for {prop.label} had vanished from sight."
    )
    world.say(
        f"Under a shelf and by a blue bell shelf, "
        f"{child.id} searched in the fading light."
    )


def mystery_turn(world: World) -> None:
    child = world.facts["child"]
    caretaker = world.facts["caretaker"]
    prop = world.facts["prop"]

    child.memes["wonder"] += 1
    caretaker.memes["worry"] += 1
    world.say(
        f'"Where did it go?" said {child.id} with a quiver and glow, '
        f'"The {prop.label} was here just today."'
    )
    world.say(
        f"{caretaker.pronoun().capitalize()} said, "
        f'"Let\'s look for a clue or a trick in the room, '
        f"and not let the old worry stay.\""
    )


def use_magic(world: World) -> None:
    child = world.facts["child"]
    caretaker = world.facts["caretaker"]
    prop = world.facts["prop"]

    prop.meters["hidden"] = 0
    prop.meters["lit"] = 1
    prop.meters["found"] = 1
    child.meters["found"] += 1
    child.memes["hope"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0
    caretaker.memes["relief"] += 1
    world.say(
        f"Then magic made a bright little spark, soft in the dark, "
        f"and the room began to hum."
    )
    world.say(
        f"The projector gave light, and the carved totem shone bright, "
        f"as if moonbeams were beating a drum."
    )


def reveal_solution(world: World) -> None:
    child = world.facts["child"]
    caretaker = world.facts["caretaker"]
    prop = world.facts["prop"]

    world.say(
        f"Behind the totem, snug and small, the {prop.label} stood tall; "
        f"its shine was a clue to the tune."
    )
    world.say(
        f"{child.id} laughed, and {caretaker.label} clapped with delight, "
        f"for the mystery solved itself soon."
    )


def ending(world: World) -> None:
    child = world.facts["child"]
    caretaker = world.facts["caretaker"]
    prop = world.facts["prop"]

    child.memes["relief"] += 1
    child.memes["pride"] += 1
    caretaker.memes["pride"] += 1
    world.say(
        f"Now {child.id} could use the {prop.label} again, "
        f"and the room felt merry and bright."
    )
    world.say(
        f"So when the small show began, the glow was grand, "
        f"and the night ended snug with a rhyme."
    )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    child = world.facts["child"]
    caretaker = world.facts["caretaker"]
    prop = world.facts["prop"]

    world.say(
        f"{child.id} was {setup_name(child.id, child.type)} in {world.setting.place}, "
        f"where magic and stories liked to stay."
    )
    world.say(
        f"{child.id} loved the {prop.label}, the cue, and the totem too, "
        f"for they made the room feel like play."
    )

    world.para()
    search_for_clue(world)
    mystery_turn(world)
    use_magic(world)
    reveal_solution(world)

    world.para()
    ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(stage).
place(attic).

prop(projector).
prop(cue).
prop(totem).

can_hide(projector).
can_hide(cue).
can_hide(totem).

holds(stage,projector). holds(stage,cue). holds(stage,totem).
holds(attic,projector). holds(attic,cue). holds(attic,totem).

valid_story(P,Pr) :- place(P), prop(Pr), holds(P,Pr).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for item in sorted(setting.holds):
            lines.append(asp.fact("holds", pid, item))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, pr) for p in SETTINGS for pr in PROPS if pr in SETTINGS[p].holds}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming mystery story for a small child about a {f["prop"].label}, a cue, and a totem.',
        f"Tell a magical story where {f['child'].id} loses the {f['prop'].label} and solves the mystery with help from a projector and a totem.",
        f"Write a simple rhyming tale with a hidden {f['prop'].label}, a clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"The {prop.label} was missing, which made {child.id} feel worried and curious.",
        ),
        QAItem(
            question=f"Who helped {child.id} look for the mystery?",
            answer=f"{caretaker.label.capitalize()} helped by staying calm and looking for a clue in the room.",
        ),
        QAItem(
            question=f"What magical thing helped solve the mystery?",
            answer=f"The projector's light helped reveal the {prop.label} behind the totem.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the {prop.label} was found?",
            answer=f"{child.id} felt relieved, proud, and happy because the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    prop = world.facts["prop"].label
    return [
        QAItem(
            question="What does a projector do?",
            answer="A projector shines light or images onto a wall so people can see them bigger.",
        ),
        QAItem(
            question="What is a cue?",
            answer="A cue is a helpful signal or pointer that shows when to begin or notice something.",
        ),
        QAItem(
            question="What is a totem?",
            answer="A totem is a carved object or symbol that can stand for a group, a place, or a story idea.",
        ),
        QAItem(
            question="Why can magic be exciting in a story?",
            answer="Magic can make surprising things happen, like revealing a hidden clue or helping solve a problem.",
        ),
        QAItem(
            question=f"Why is it special when the {prop} is found?",
            answer="Finding the missing thing ends the worry and lets the characters enjoy the moment together.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming magical mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--prop", choices=PROPS.keys())
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker-type", choices=["mother", "father"])
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
    prop = args.prop or rng.choice(list(PROPS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    caretaker_type = args.caretaker_type or rng.choice(["mother", "father"])
    if prop == "cue" and place == "attic":
        pass
    name = args.name or rng.choice(NAMES[child_type])
    return StoryParams(
        place=place,
        child_name=name,
        child_type=child_type,
        caretaker_type=caretaker_type,
        prop=prop,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        combos = asp_valid_stories()
        print(f"{len(combos)} valid (place, prop) combos:\n")
        for place, prop in combos:
            print(f"  {place:7} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="stage", child_name="Mia", child_type="girl", caretaker_type="mother", prop="projector"),
            StoryParams(place="attic", child_name="Theo", child_type="boy", caretaker_type="father", prop="cue"),
            StoryParams(place="stage", child_name="Nora", child_type="girl", caretaker_type="mother", prop="totem"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
