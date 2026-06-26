#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/like_bus_depot_repetition_comedy.py
===============================================================================================================

A small comedy storyworld set in a bus depot, built from a seed that leans on
repetition: the same mistake is made, noticed, and corrected in a funny loop
until the characters finally get it right.

The world model tracks physical meters and emotional memes:
- meters: location, carried items, queue state, loudness, tidiness
- memes: patience, confusion, delight, embarrassment, relief, trust

The story premise:
A child and a grown-up are at a bus depot with the wrong ticket, the wrong bag,
or the wrong idea. An announcement repeats. A mistake repeats. A joke-like
pattern repeats. Then the characters notice the pattern, fix it, and board the
bus with a silly little victory.

The seed word is "like", which appears naturally in the repeated spoken lines
and the child's comparisons.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the bus depot"
    has_ticket_window: bool = True
    has_platform: bool = True
    has_bench: bool = True
    has_announcement_board: bool = True


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    kind: str
    plural: bool = False
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    object: str
    child_name: str
    child_type: str
    adult_type: str
    tone: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.announcement_count = 0
        self.mistake_count = 0
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.announcement_count = self.announcement_count
        clone.mistake_count = self.mistake_count
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _repeat_line(base: str, n: int) -> str:
    return " ".join([base] * n)


def _announce(world: World) -> str:
    world.announcement_count += 1
    if world.announcement_count == 1:
        return "Final call for the downtown line."
    if world.announcement_count == 2:
        return "Final call for the downtown line."
    if world.announcement_count == 3:
        return "Final final call for the downtown line."
    return "Final final call for the downtown line."


def _do_comedy_mixup(world: World) -> None:
    for ent in world.characters():
        ent.memes["confusion"] = ent.memes.get("confusion", 0) + 1
        ent.memes["embarrassment"] = ent.memes.get("embarrassment", 0) + 0.5


def _resolve_mixup(world: World) -> None:
    for ent in world.characters():
        ent.memes["confusion"] = 0
        ent.memes["relief"] = ent.memes.get("relief", 0) + 1
        ent.memes["delight"] = ent.memes.get("delight", 0) + 1


def _safety_gate(world: World) -> bool:
    return world.place.has_platform and world.place.has_announcement_board


def tell(params: StoryParams) -> World:
    world = World(PLACE)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult_type))
    obj_spec = OBJECTS[params.object]
    obj = world.add(Entity(
        id="Object",
        kind="thing",
        type=obj_spec.kind,
        label=obj_spec.label,
        phrase=obj_spec.phrase,
        owner=child.id,
        caretaker=adult.id,
        plural=obj_spec.plural,
    ))
    obj.carried_by = child.id

    child.meters["waiting"] = 1
    adult.meters["waiting"] = 1
    child.memes["patience"] = 1
    adult.memes["patience"] = 1

    # Act 1: setup
    world.say(f"{child.id} and {child.pronoun('possessive')} {params.adult_type} were at {world.place.name}.")
    world.say(f"{child.id} liked the depot because it was busy and a little bouncy, like a machine that forgot to be quiet.")
    world.say(f"{child.id} was carrying {obj.phrase}, and {child.pronoun('subject').capitalize()} kept saying {repr('like')} in a bright, joking way.")

    # Act 2: repeated confusion
    world.para()
    if _safety_gate(world):
        world.say(_announce(world))
        world.say(f"{params.adult_type.capitalize()} heard it and said, 'Wait, did they say the downtown line, or did they say it like they said it last time?'")
        world.say(f"{child.id} looked at the board and pointed at the same sign again. 'Like that one,' {child.pronoun('subject')} said.")
        _do_comedy_mixup(world)
        world.mistake_count += 1
        world.say(f"Then the little slip happened again: the ticket in {child.pronoun('possessive')} hand was for the wrong bus, so they both looked at it, then at the board, then back at it.")
        world.say(f"The adult checked the ticket a second time. It was still the wrong one.")
        world.say(f"The child checked it a third time. It was still the wrong one, which was so funny that {child.id} snorted.")
        world.say(_announce(world))
        world.say(f"That made the problem even sillier, because now the depot sounded like a joke told twice.")
    else:
        raise StoryError("This story needs a bus depot with a platform and repeated announcements.")

    # Act 3: correction and payoff
    world.para()
    if obj_spec.kind == "ticket":
        world.say(f"At last, {params.adult_type} compared the ticket to the board and realized the mistake: the ticket was for the east line, not the downtown line.")
        world.say(f"{child.id} laughed and said, 'Oh! Like the other one, but not the same one.'")
    elif obj_spec.kind == "bag":
        world.say(f"At last, {params.adult_type} found the label on the bag and realized it had been swapped with a very similar one.")
        world.say(f"{child.id} laughed and said, 'It looked like ours, but it was the other bag.'")
    else:
        world.say(f"At last, {params.adult_type} noticed the sign in the {obj_spec.label} and realized the mix-up had been hiding in plain sight.")
        world.say(f"{child.id} laughed and said, 'It was like a clue wearing a hat.'")

    _resolve_mixup(world)
    world.say(f"So they fixed the mistake, kept the real {obj_spec.label}, and joined the line again.")
    world.say(f"This time the bus arrived, the doors sighed open, and the repeated announcement finally turned into a ride.")
    world.say(f"{child.id} climbed aboard with a grin, still saying {repr('like')} once, softly, like a tiny joke that had finally found its seat.")

    world.facts.update(
        child=child,
        adult=adult,
        object=obj,
        params=params,
        place=params.place,
        object_spec=obj_spec,
        announced=world.announcement_count,
        mistakes=world.mistake_count,
        resolved=True,
    )
    return world


PLACE = Place()

OBJECTS = {
    "ticket": ObjectSpec(
        label="ticket",
        phrase="a paper ticket with a blue stripe",
        kind="ticket",
        helps={"boarding"},
    ),
    "bag": ObjectSpec(
        label="bag",
        phrase="a striped travel bag",
        kind="bag",
        helps={"carrying"},
    ),
    "snack": ObjectSpec(
        label="snack box",
        phrase="a snack box wrapped in yellow paper",
        kind="snack",
        helps={"waiting"},
    ),
}

CHILD_NAMES = ["Milo", "Nina", "Pip", "Tessa", "Jo", "Ravi", "Luna", "Omar"]
CHILD_TYPES = ["boy", "girl"]
ADULT_TYPES = ["mother", "father", "aunt", "uncle"]
TONES = ["playful", "cheerful", "bouncy", "silly"]


def valid_combos() -> list[tuple[str, str]]:
    return [(PLACE.name, obj_id) for obj_id in OBJECTS]


@dataclass
class StoryParams:
    place: str
    object: str
    child_name: str
    child_type: str
    adult_type: str
    tone: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set in a bus depot with repetition.")
    ap.add_argument("--place", choices=["bus_depot"])
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("--tone", choices=TONES)
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
    place = "bus_depot"
    obj = args.object or rng.choice(list(OBJECTS))
    child_type = args.gender or rng.choice(CHILD_TYPES)
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_type = args.adult or rng.choice(ADULT_TYPES)
    tone = args.tone or rng.choice(TONES)
    return StoryParams(place=place, object=obj, child_name=child_name, child_type=child_type, adult_type=adult_type, tone=tone)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedy story set in a bus depot where the word "like" keeps showing up.',
        f"Tell a funny story about {f['child'].id} and {f['adult'].type} in a bus depot with repeated announcements.",
        f"Write a child-friendly repetition comedy about a {f['object_spec'].kind} mix-up at a bus depot.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    obj = f["object"]
    return [
        QAItem(
            question=f"Where were {child.id} and {adult.type} when the mix-up happened?",
            answer="They were at the bus depot, where buses came and went and announcements repeated.",
        ),
        QAItem(
            question=f"What kept being repeated in the story?",
            answer="The announcement repeated, and the mistake was checked more than once, which made the scene feel funny.",
        ),
        QAItem(
            question=f"What did {child.id} keep saying in the story?",
            answer="The child kept saying like, and even the joking comparisons sounded like part of the rhythm of the day.",
        ),
        QAItem(
            question=f"What did they finally fix before boarding?",
            answer=f"They fixed the wrong {obj.label} or ticket mix-up, then joined the line again and boarded the bus.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, wait, and get ready to leave with passengers.",
        ),
        QAItem(
            question="Why do announcements repeat at a depot?",
            answer="Announcements repeat so people can hear the important information even if they missed it the first time.",
        ),
        QAItem(
            question="Why can a repeated mistake be funny in a story?",
            answer="A repeated mistake can be funny because the characters keep noticing the same problem and trying again in a silly way.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  announcements: {world.announcement_count}")
    lines.append(f"  mistakes: {world.mistake_count}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, O) :- place(P), object(O).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "bus_depot")]
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: this bus depot comedy needs a simple object mix-up that can be fixed after repeated announcements.)"


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


CURATED = [
    StoryParams(place="bus_depot", object="ticket", child_name="Milo", child_type="boy", adult_type="mother", tone="silly"),
    StoryParams(place="bus_depot", object="bag", child_name="Nina", child_type="girl", adult_type="father", tone="bouncy"),
    StoryParams(place="bus_depot", object="snack", child_name="Pip", child_type="boy", adult_type="aunt", tone="cheerful"),
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
