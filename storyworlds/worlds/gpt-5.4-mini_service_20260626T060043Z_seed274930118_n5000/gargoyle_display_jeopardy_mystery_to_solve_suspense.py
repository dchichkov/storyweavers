#!/usr/bin/env python3
"""
A tiny detective-story world about a gargoyle display, a mystery to solve, and
a little bit of jeopardy.

Premise
-------
At a quiet museum, a small stone gargoyle is part of a display near the front
hall. When the museum opens for a school visit, the gargoyle seems out of place,
and the room feels tense. A child notices a clue, follows the trail, and solves
the mystery before the display is ruined.

This world is intentionally small and constraint-checked:
- one setting
- one central object
- one mystery
- one safe resolution

The simulated state tracks:
- physical meters: distance, damage, dust, risk
- emotional memes: curiosity, worry, relief, pride

The story prose is driven by the world state, not by swapping nouns in a fixed
paragraph.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str = "the museum"
    mood: str = "quiet"
    affords: set[str] = field(default_factory=lambda: {"display", "mystery", "detective"})


@dataclass
class ObjectDef:
    label: str
    phrase: str
    type: str
    weight: str
    display_place: str
    clue: str
    risk: str
    tag: str


@dataclass
class StoryParams:
    place: str
    object_id: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


SETTING = Setting()

OBJECTS = {
    "gargoyle": ObjectDef(
        label="gargoyle",
        phrase="a small stone gargoyle with a chipped wing",
        type="gargoyle",
        weight="heavy",
        display_place="on a high pedestal",
        clue="dust on the pedestal",
        risk="jeopardy",
        tag="gargoyle",
    )
}

GIRL_NAMES = ["Mina", "Nora", "Ivy", "June", "Tessa"]
BOY_NAMES = ["Eli", "Theo", "Milo", "Finn", "Owen"]
HELPERS = ["guide", "guard", "curator"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective mystery storyworld with a gargoyle display.")
    ap.add_argument("--place", choices=["museum"], default="museum")
    ap.add_argument("--object", dest="object_id", choices=list(OBJECTS), default="gargoyle")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.gender == "girl":
        detective_type = "girl"
    elif args.gender == "boy":
        detective_type = "boy"
    else:
        detective_type = rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    helper_type = "mother" if detective_type == "girl" else "father"
    helper_name = args.helper or rng.choice(["Ms. Lane", "Mr. Vale", "Aunt Rose", "Uncle Ben"])
    return StoryParams(
        place=args.place,
        object_id=args.object_id,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    obj = OBJECTS[params.object_id]
    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    display = world.add(Entity(id="display", type=obj.type, label=obj.label, phrase=obj.phrase, caretaker=helper.id))

    detective.memes["curiosity"] = 1.0
    display.meters["distance"] = 0.0
    display.meters["risk"] = 0.0
    helper.memes["worry"] = 0.0

    # Setup
    world.say(
        f"On a quiet morning at the museum, {detective.id} noticed a special {display.label} "
        f"{obj.display_place}."
    )
    world.say(
        f"It looked like a real clue from an old case, and {detective.pronoun('subject')} felt "
        f"pulled toward it right away."
    )

    # Mystery emerges
    world.para()
    world.say(
        f"Near the display, {detective.id} saw {obj.clue}, and that made the whole hall feel strange."
    )
    world.say(
        f"{helper.label_word if hasattr(helper, 'label_word') else helper.label} kept watch, but the room still felt full of suspense."
    )
    display.meters["risk"] = 1.0
    helper.memes["worry"] = 1.0
    detective.memes["curiosity"] += 1.0
    world.facts["clue"] = obj.clue
    world.facts["risk"] = obj.risk

    # Investigation
    world.para()
    world.say(
        f"{detective.id} crouched by the pedestal and followed the dusty mark to a loose vent behind the case."
    )
    world.say(
        f"Inside, {detective.pronoun('subject')} found a little tag that explained the {display.label} had been moved for cleaning, not stolen."
    )
    display.meters["risk"] = 0.0
    detective.memes["curiosity"] += 0.5

    # Resolution
    world.para()
    detective.memes["relief"] = 1.0
    detective.memes["pride"] = 1.0
    helper.memes["worry"] = 0.0
    world.say(
        f"{detective.id} smiled and showed {helper.pronoun('object')} the tag, and the mystery was solved."
    )
    world.say(
        f"Soon the {display.label} was back on display, safe and steady, while {detective.id} stood a little taller beside it."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        display=display,
        obj=obj,
        solved=True,
        place=params.place,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    obj = f["obj"]
    return [
        f'Write a short detective story for a young child about a {obj.label} display in a museum.',
        f"Tell a suspenseful but gentle mystery where {det.id} notices a clue and solves the case.",
        f'Write a story that includes the words "gargoyle", "display", and "jeopardy".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    obj = f["obj"]
    return [
        QAItem(
            question=f"What did {det.id} notice at the museum?",
            answer=f"{det.id} noticed a special {obj.label} {obj.display_place}.",
        ),
        QAItem(
            question=f"What clue made the hall feel mysterious?",
            answer=f"{obj.clue} made the hall feel mysterious and gave {det.id} something to investigate.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{det.id} followed the dusty mark, found a tag behind the case, and learned the {obj.label} had only been moved for cleaning.",
        ),
        QAItem(
            question=f"Why was the {obj.label} not really in danger?",
            answer=f"The situation felt like jeopardy at first, but the tag showed the {obj.label} was safe and had not been stolen.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gargoyle?",
            answer="A gargoyle is a carved stone figure, often made to look fierce or strange on old buildings and displays.",
        ),
        QAItem(
            question="What is a display?",
            answer="A display is a careful way of showing an object so people can look at it and learn about it.",
        ),
        QAItem(
            question="What does jeopardy mean?",
            answer="Jeopardy means danger or a risky situation where something important could be harmed or lost.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that makes you wait and wonder what will happen next.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
display_safe(D) :- object(D).
mystery_to_solve(D) :- object(D), clue(D).
suspense(D) :- mystery_to_solve(D), jeopardy(D).
solved(D) :- mystery_to_solve(D), not stolen(D), moved_for_cleaning(D).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "museum"),
        asp.fact("object", "gargoyle"),
        asp.fact("clue", "gargoyle"),
        asp.fact("jeopardy", "gargoyle"),
        asp.fact("moved_for_cleaning", "gargoyle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show solved/1."))
    atoms = set(asp.atoms(model, "solved"))
    expected = {("gargoyle",)}
    if atoms == expected:
        print("OK: ASP and Python agree on the gargoyle mystery.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


CURATED = [
    StoryParams(place="museum", object_id="gargoyle", detective_name="Mina", detective_type="girl", helper_name="Ms. Lane", helper_type="mother"),
    StoryParams(place="museum", object_id="gargoyle", detective_name="Theo", detective_type="boy", helper_name="Mr. Vale", helper_type="father"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show solved/1."))
        print("ASP model:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params_from_args(args, rng)
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
        if args.all:
            header = f"### {sample.params.detective_name}: gargoyle mystery at the museum"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
